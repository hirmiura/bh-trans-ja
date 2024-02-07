#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""JSON Pointerを定義する"""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from itertools import chain


class JsonPointer:
    """JSON Pointerを表すクラス

    Raises:
        JsonPointerError: 不正なエスケープ
        JsonPointerError: 「/」で開始しなければならない
        JsonPointerError: サポートされない型
    """

    _CRE_INVALID_ESCAPE = re.compile("(~[^01]|~$)")  # 不正なエスケープ

    def __init__(self, pointer: str | Sequence[str]) -> None:
        """JsonPointerオブジェクトを作る

        Args:
            pointer (str | Sequence):
                JSON Pointerを表すエスケープ済み文字列、または未エスケープシーケンス

        Raises:
        JsonPointerError: 不正なエスケープ
        JsonPointerError: 「/」で開始しなければならない
        TypeError: サポートされない型
        """
        parts: list[str]
        if isinstance(pointer, str):
            # 不正なエスケープを含んでいないかチェックする
            invalid_escape = self._CRE_INVALID_ESCAPE.search(pointer)
            if invalid_escape:
                raise JsonPointerError(f"不正なエスケープを含んでいます {invalid_escape.group()}")
            # パーツに分解する
            parts = pointer.split("/")
            if parts.pop(0) != "":
                raise JsonPointerError(f"ポインタは「/」で開始しなければなりません {pointer}")
            parts = [JsonPointer.unescape(p) for p in parts]
        elif isinstance(pointer, Sequence):
            parts = list(pointer)
        else:
            raise TypeError(f"サポートされない型です {pointer}")

        path = "".join(["/" + JsonPointer.escape(p) for p in parts])
        self._path = path
        self._parts = parts

    @property
    def path(self) -> str:
        """JSON Pointerの文字列表現を返す

        Returns:
            str: 文字列表現
        """
        return self._path

    @property
    def parts(self) -> list[str]:
        """JSON Pointerの未エスケープの文字列リスト表現を返す

        Returns:
            list[str]: 文字列リスト表現
        """
        return self._parts

    def __eq__(self, other):  # noqa: D105
        if not isinstance(other, JsonPointer):
            return False
        return self.parts == other.parts

    def __hash__(self):  # noqa: D105
        return hash(tuple(self.parts))

    def __str__(self):  # noqa: D105
        return self.path

    def __repr__(self):  # noqa: D105
        return "JsonPointer(" + repr(self.path) + ")"

    def __truediv__(self, addition):  # noqa: D105
        return self.join(addition)

    def join(self, addition: JsonPointer | Sequence[str] | str) -> JsonPointer:
        """末尾にパスを追加した新しいJsonPointerオブジェクトを返す

        Args:
            addition (JsonPointer | Sequence[str] | str): 末尾に追加するパス

        Raises:
            TypeError: サポートされない型
            JsonPointerError: 追加パスに問題があった場合

        Returns:
            JsonPointer: パスを追加した新しいオブジェクト
        """
        if isinstance(addition, JsonPointer):
            suffix_parts = addition.parts
        elif isinstance(addition, str):
            suffix_parts = addition.split("/")
            if suffix_parts[0] == "":
                suffix_parts.pop(0)
        elif isinstance(addition, Sequence):
            suffix_parts = list(addition)
        else:
            raise TypeError(f"サポートされない型です {addition}")
        try:
            parts = list(chain(self.parts, suffix_parts))
            return JsonPointer(parts)
        except Exception:
            raise JsonPointerError(f"追加パスに問題があります {addition}")

    @staticmethod
    def escape(s: str) -> str:
        """JSON Pointer形式でエスケープする

        Args:
            s (str): エスケープ対象オブジェクト

        Returns:
            str: エスケープ済みオブジェクト
        """
        return s.replace("~", "~0").replace("/", "~1")

    @staticmethod
    def unescape(s: str) -> str:
        """JSON Pointer形式でアンエスケープする

        Args:
            s (str): アンエスケープ対象オブジェクト

        Returns:
            str: アンエスケープ済みオブジェクト
        """
        return s.replace("~1", "/").replace("~0", "~")


class JsonPointerError(Exception):
    """JsonPointerクラスで発生するエラーを表すクラス"""

    pass


def main() -> int:
    """メイン関数

    Returns:
        int: 成功時は0を返す
    """
    ptr = JsonPointer([])
    print(repr(ptr))
    print(ptr.parts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
