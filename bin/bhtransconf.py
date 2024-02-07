#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""設定ファイルを定義する"""
from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel


class BhTransConf(BaseModel):
    """設定"""

    input_json: str
    output_pot: str

    input_mo: str
    output_json: str
    output_culture: str

    pid_version: str = "0.1"

    rules: dict[str, BhTransConfRule]

    @classmethod
    def load(cls, path: Path) -> BhTransConf:
        """設定ファイルを読み込む

        Args:
            path (Path): パス

        Returns:
            BhTransConf: 設定の入ったオブジェクト
        """
        with path.open("rb") as fp:  # バイナリモードで開く
            toml_obj = tomllib.load(fp)
        return cls(**toml_obj)


class BhTransConfRule(BaseModel):
    """ルール"""

    msgctxt: bool = False
    extracts: list[str]


if __name__ == "__main__":
    conf = BhTransConf.load(Path("bhtrans.toml"))
    import json
    import sys

    json.dump(conf.model_dump(), sys.stdout, indent=4)
