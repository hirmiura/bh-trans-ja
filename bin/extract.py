#!/usr/bin/env -S python3
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""Book of HoursのJSONデータを抽出する"""

from __future__ import annotations

import argparse
import json
import re
import sys
from logging import DEBUG, StreamHandler, getLogger
from pathlib import Path
from typing import Any

import chardet
import dirtyjson

logger = getLogger(__name__)
handler = StreamHandler(sys.stderr)
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


ORIGINAL_FILE_KEY = "orignal_file"
INHERITS_KEY = "inherits"

CC_RESET = "\033[0m"
CC_RED = "\033[91m"
CC_GREEN = "\033[92m"
CC_YELLOW = "\033[93m"

type BhObjT = dict[str, list[dict[str, Any]]]  # type: ignore
type CoreObjT = dict[str, dict[str, dict[str, Any]]]  # type: ignore

bhdata: CoreObjT = {}

input_paths: list[str] = []
output_file: Path = Path("bhdata.json")
ignores: list[str] = [
    r"(?i)(?<!\.json)$",  # 拡張子json以外は無視
    r"core/cultures/(?!en/)[^/]*/",  # en以外のculturesは無視
]
xignores: list[re.Pattern[str]] = []  # コンパイル済み


def procee_args() -> argparse.Namespace:
    """コマンドライン引数を処理する

    Returns:
        argparse.Namespace: 処理した引数
    """
    global ignores
    parser = argparse.ArgumentParser(description="Book of Hours のデータベースを作成する")
    parser.add_argument(
        metavar="PATH", dest="paths", nargs="+", help="調査対象のディレクトリやファイル"
    )
    parser.add_argument("-o", dest="output_file", action="store", help="データを出力するファイル")
    parser.add_argument(
        "-i",
        "--ignore",
        dest="ignores",
        metavar="REPATH",
        action="append",
        default=ignores,
        help="無視するファイルパス(正規表現)。複数の -i が可能",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args()

    # グローバル変数へ入れる
    global input_paths, output_file, xignores
    input_paths = args.paths or input_paths
    output_file = Path(args.output_file) if args.output_file else output_file
    ignores = args.ignores or ignores
    xignores = compile_ignores(ignores)

    return args


def procee() -> int:
    """処理の大元となる関数

    Returns:
        int: 成功時は0を返す
    """
    # パスを走査する
    global input_paths
    for p in input_paths:
        path = Path(p)
        ret = scan_and_process(path)
        if ret != 0:
            return ret
    save_data()  # 保存
    return 0


def compile_ignores(ignores: list[str]) -> list[re.Pattern[str]]:
    """無視リストの正規表現をコンパイルする

    Args:
        ignores (list[str]): 無視リスト

    Returns:
        list[re.Pattern[str]]: コンパイルされた無視リスト
    """
    assert ignores is not None
    xignores = []
    if ignores:
        for ig in ignores:
            xignores.append(re.compile(ig))
    return xignores


def scan_and_process(path: Path) -> int:
    """パスを走査してファイルを処理する

    Args:
        path (Path): 対象となるパス

    Returns:
        int: 成功時は0を返す
    """
    assert path
    if not path.exists():
        logger.error("%s%sが存在しません%s", CC_RED, path, CC_RESET)
        return 1
    if path.is_dir():  # ディレクトリの場合
        for dp, _, fns in path.walk():
            for fn in fns:
                file = dp / fn
                check_and_process(file)
    elif path.is_file():  # ファイルの場合
        check_and_process(path)
    else:
        logger.error("%s%sがファイルでもディレクトリでもありません%s", CC_RED, path, CC_RESET)
        return 2
    return 0


def check_and_process(file: Path) -> None:
    """無視リストをチェックした後、ファイルを読み込んで処理する

    Args:
        file (Path): ファイル
    """
    assert file
    global xignores
    assert xignores is not None
    if should_ignore(file, xignores):
        logger.info("%s%sを無視しました%s", CC_GREEN, file, CC_RESET)
    else:
        obj = read_file(file)
        assemble_data(obj, str(file))


def should_ignore(file: Path, xignores: list[re.Pattern[str]]) -> bool:
    """ファイルパスが無視リストに含まれているか判定する

    Args:
        file (Path): ファイル
        xignores (list[re.Pattern[str]]): 無視リスト

    Returns:
        bool: 無視すべきならTrue
    """
    assert file
    assert xignores is not None
    path = str(file)
    for repath in xignores:
        if repath.search(path):
            return True
    return False


def read_file(file: Path) -> Any:
    """JSONファイルを読み込む

    Args:
        file (Path): JSONファイル

    Returns:
        Any: ファイルの内容のオブジェクト
    """
    assert file
    byte_str = file.read_bytes()  # バイナリで読み込む
    result = chardet.detect(byte_str)["encoding"] or "utf-8"  # エンコーディングの推定
    logger.debug("%s (%s)", file, result)
    text = byte_str.decode(encoding=result)  # デコードする
    obj = dirtyjson.loads(text)  # jsonとし読み込む
    return obj


def assemble_data(obj: BhObjT, file: str | None = None) -> None:
    """データを追加していく

    Args:
        obj (dict[str, list[dict[str, Any]]]): オブジェクト
        file (str | None, optional): 記述されていたファイル。デフォルト:None.
    """
    assert obj
    global bhdata
    assert bhdata is not None
    obj = {k.lower(): v for k, v in obj.items()}  # keyを小文字にする
    for grp, val in obj.items():
        if grp not in bhdata:  # grpがなければ作る
            bhdata[grp] = {}
        bhgrp = bhdata[grp]
        for item in val:  # リストを処理
            low = {k.lower(): v for k, v in item.items()}  # keyを小文字にする
            if "id" in low:
                id = low["id"]
                if id in bhgrp:
                    logger.warning("%s重複ID(%s)をスキップします%s", CC_YELLOW, id, CC_RESET)
                    if ORIGINAL_FILE_KEY in bhgrp[id]:
                        logger.debug(
                            "%s重複先: %s%s", CC_YELLOW, bhgrp[id][ORIGINAL_FILE_KEY], CC_RESET
                        )
                else:
                    bhgrp[id] = low
                    if file:
                        if ORIGINAL_FILE_KEY in bhgrp[id]:
                            logger.warning(
                                "%s%sに%sが既にあるためスキップします%s",
                                CC_YELLOW,
                                id,
                                ORIGINAL_FILE_KEY,
                                CC_RESET,
                            )
                        else:
                            bhgrp[id][ORIGINAL_FILE_KEY] = file
            else:
                logger.warning("%sidが無いためスキップします%s", CC_YELLOW, CC_RESET)


def save_data() -> None:
    """データをファイルに保存する"""
    global bhdata, output_file
    assert bhdata
    assert output_file
    # jsonを書き出す
    with output_file.open("w", encoding="utf-8") as fp:
        json.dump(bhdata, fp, ensure_ascii=False, separators=(",", ":"))
    logger.info("%s に出力しました", output_file)


def main() -> int:
    """メイン関数

    Returns:
        int: 成功時は0を返す
    """
    procee_args()
    return procee()


if __name__ == "__main__":
    sys.exit(main())
