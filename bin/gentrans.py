#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""翻訳JSONファイルを生成する"""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from datetime import timedelta, timezone
from gettext import GNUTranslations
from logging import DEBUG, StreamHandler, getLogger
from pathlib import Path
from typing import Any

from bhtransconf import BhTransConf
from extract import BhObjT, CoreObjT
from jsonpointer import JsonPointer
from walk import walk

logger = getLogger(__name__)
handler = StreamHandler(sys.stderr)
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

DEFAULT_CONFIG_FILE = "bhtrans.toml"
TZ = timezone(timedelta(hours=+9), "JST")

CC_RESET = "\033[0m"
CC_RED = "\033[91m"
CC_GREEN = "\033[92m"
CC_YELLOW = "\033[93m"

config: BhTransConf


def pargs() -> argparse.Namespace:
    """コマンドライン引数を処理する

    Returns:
        argparse.Namespace: 処理した引数
    """
    parser = argparse.ArgumentParser(description="翻訳JSONファイルを生成する")
    parser.add_argument(
        "-c",
        "--conf",
        default=DEFAULT_CONFIG_FILE,
        help="設定ファイル。デフォルト:%(default)s",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args()

    # 設定ファイルを読み込む
    global config
    conf_file = args.conf or DEFAULT_CONFIG_FILE
    config = BhTransConf.load(Path(conf_file))
    logger.info("設定ファイル(%s)を読み込みました", conf_file)

    return args


def process() -> int:
    """処理の大元となる関数

    Returns:
        int: 成功時は0を返す
    """
    # core.jsonを読み込む
    core_obj: CoreObjT = json.loads(Path(config.input_json).read_text())
    logger.info("JSONファイル(%s)を読み込みました", config.input_json)
    trans_obj: CoreObjT = {}

    # moファイルを読み込む
    with Path(config.input_mo).open("rb") as fpmo:
        # gettextを読み込む
        gtr = GNUTranslations(fp=fpmo)
        logger.info("MOファイル(%s)を読み込みました", config.input_mo)

    # グループ(タイプ)毎に処理する
    for grp, rule in config.rules.items():
        logger.info("グループ(%s)を処理しています", grp)
        if grp not in core_obj:
            logger.warning("%s%sが無いためスキップします%s", CC_YELLOW, grp, CC_RESET)
            continue  # grpが無ければスキップ
        cre_extracts = [re.compile(ptn) for ptn in rule.extracts]  # 正規表現をコンパイル
        obj = core_obj[grp]

        # オブジェクトを走査する
        for wp in walk(obj):
            # JSON Pointerがマッチするか
            is_match = any(cre.search(wp.pointer.path) for cre in cre_extracts)
            if not is_match:
                continue  # マッチしなければスキップ
            text = str(wp.objects[-1])
            if len(str.strip(text)) == 0:
                continue  # 空および空白のみの場合もスキップ

            # 翻訳する
            path = (JsonPointer((grp,)) / wp.pointer).path
            # logger.debug("マッチしました %s: %s", path, text)
            if rule.msgctxt:  # コンテキストが必要か？
                tr_text = gtr.pgettext(path, text)
            else:
                tr_text = gtr.gettext(text)
            if text == tr_text:  # 翻訳されているか比較
                continue  # 同じならスキップ

            # 翻訳済みオブジェクトを作る
            id = wp.pointer.parts[0]
            if grp not in trans_obj:
                trans_obj[grp] = {}
            if id not in trans_obj[grp]:
                trans_obj[grp][id] = {}
            if "id" not in trans_obj[grp][id]:
                trans_obj[grp][id]["id"] = id

            has_list = False
            parent: Any = trans_obj[grp]
            core_parent: Any = core_obj[grp]
            for p, t, o in zip(wp.pointer.parts, wp.types[1:], wp.objects[1:]):
                parent_type = type(parent)
                if parent_type == dict:
                    if not has_list:
                        if t == dict:
                            if p not in parent:
                                parent[p] = {}
                        elif t == list:
                            if p not in parent:
                                parent[p] = deepcopy(core_parent[p])
                            has_list = True
                    if t != dict and t != list:
                        parent[p] = tr_text
                elif parent_type == list:
                    if t != dict and t != list:
                        parent[int(p)] = tr_text

                if parent_type == dict:
                    parent = parent[p]
                    core_parent = core_parent[p]
                elif parent_type == list:
                    parent = parent[int(p)]
                    core_parent = core_parent[int(p)]

    save_culture(trans_obj, core_obj)
    save_others(trans_obj, core_obj)

    return 0


def save_culture(trans_obj: CoreObjT, core_obj: CoreObjT):
    """cultureファイルを保存する

    Args:
        trans_obj (CoreObjT): 翻訳済みオブジェクト
        core_obj (CoreObjT): 元オブジェクト
    """
    assert trans_obj
    assert core_obj
    # culturesの処理
    culture_obj: BhObjT = {"cultures": []}
    culture_obj["cultures"].append(deepcopy(core_obj["cultures"]["en"]))
    culture_obj["cultures"][0]["endonym"] = "日本語"
    culture_obj["cultures"][0]["exonym"] = "Japanese"
    culture_obj["cultures"][0]["fontscript"] = "jp"
    if "cultures" in trans_obj:
        if "en" in trans_obj["cultures"]:
            # cultureは未翻訳部分もenから引き継ぐ
            culture_obj["cultures"][0] = merge_dict(
                culture_obj["cultures"][0], trans_obj["cultures"]["en"]
            )
            culture_obj["cultures"][0]["id"] = "ja"  # idを上書き
            # ファイルに保存する
            Path(config.output_culture).write_text(
                json.dumps(culture_obj, ensure_ascii=False, separators=(",", ":"))
            )
            logger.info("%s に出力しました", config.output_culture)
        del trans_obj["cultures"]


def save_others(trans_obj: CoreObjT, core_obj: CoreObjT):
    """culture以外を保存する

    Args:
        trans_obj (CoreObjT): 翻訳済みオブジェクト
        core_obj (CoreObjT): 元オブジェクト
    """
    assert trans_obj
    assert core_obj
    for grp in trans_obj:
        bh_obj: BhObjT = {}
        if grp == "cultures":
            continue
        if grp not in bh_obj:
            bh_obj[grp] = []
        for v in trans_obj[grp].values():
            bh_obj[grp].append(v)
        # ファイルに保存する
        file = config.output_json_prefix + grp + ".json"
        Path(file).write_text(json.dumps(bh_obj, ensure_ascii=False, separators=(",", ":")))
        logger.info("%s に出力しました", file)


def merge_dict(d1: dict, d2: dict) -> dict:
    """2つの辞書を再帰マージして返す

    Args:
        d1 (dict): ベース辞書
        d2 (dict): 追加辞書

    Returns:
        dict: マージ辞書
    """
    ret = d1.copy()
    for k, v in d2.items():
        if isinstance(v, dict) and isinstance(ret[k], dict):
            ret[k] = merge_dict(ret[k], v)
        else:
            ret[k] = v
    return ret


def main() -> int:
    """メイン関数

    Returns:
        int: 成功時は0を返す
    """
    pargs()
    result = process()
    return result


if __name__ == "__main__":
    sys.exit(main())
