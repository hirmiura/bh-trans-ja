#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""JSON Pointerを定義する"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from itertools import chain
from typing import Any

from .exceptions import JPtrException, JPtrInvalidEscapeError, JPtrNotSlashStartError, JPtrTypeError


class JsonPointer:
    """JSON Pointerを表すクラス"""

    _CRE_INVALID_ESCAPE = re.compile("(~[^01]|~$)")  # 不正なエスケープ

    def __init__(self, pointer: str | Sequence[str]) -> None:
        """JsonPointerオブジェクトを作る

        Args:
            pointer (str | Sequence):
                JSON Pointerを表すエスケープ済み文字列、または未エスケープシーケンス

        Raises:
        JPtrInvalidEscapeError: 不正なエスケープ
        JPtrNotSlashStartError: 「/」で開始しなければならない
        JPtrTypeError: サポートされない型
        """
        parts: list[str]
        if isinstance(pointer, str):
            #### 文字列の場合 ####
            # 不正なエスケープを含んでいないかチェックする
            invalid_escape = self._CRE_INVALID_ESCAPE.search(pointer)
            if invalid_escape:
                raise JPtrInvalidEscapeError(None, invalid_escape.group())
            # パーツに分解する
            parts = pointer.split("/")
            if parts.pop(0) != "":
                raise JPtrNotSlashStartError(None, pointer)
            parts = [JsonPointer.unescape(p) for p in parts]
        elif isinstance(pointer, Sequence):
            #### シーケンスの場合 ####
            parts = list(pointer)
        else:
            #### その他の場合 ####
            raise JPtrTypeError(None, pointer)

        path: str = "".join(["/" + JsonPointer.escape(p) for p in parts])
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
            JPtrTypeError: サポートされない型
            JPtrException: 追加パスに問題があった場合

        Returns:
            JsonPointer: パスを追加した新しいオブジェクト
        """
        match addition:
            case JsonPointer():
                #### JsonPointerの場合 ####
                suffix_parts = addition.parts

            case str():
                #### 文字列の場合 ####
                suffix_parts = addition.split("/")
                if suffix_parts[0] == "":
                    suffix_parts.pop(0)

            case Sequence():
                #### シーケンスの場合 ####
                suffix_parts = list(addition)

            case _:
                #### その他の場合 ####
                raise JPtrTypeError(None, addition)

        try:
            parts = list(chain(self.parts, suffix_parts))
            return JsonPointer(parts)

        except Exception as e:
            raise JPtrException("追加パスに問題があります", addition) from e

    def get(self, obj: Any) -> Any:
        """このJSON Pointerに合致するオブジェクトを取得する

        Args:
            obj (Any): 走査対象のオブジェクト

        Raises:
            JPtrTypeError: サポートされない型

        Returns:
            Any: 取得したオブジェクト
        """
        for p in self.parts:
            match obj:
                case Mapping():
                    obj = obj[p]
                case Sequence():
                    obj = obj[int(p)]
                case _:
                    raise JPtrTypeError(None, obj)
        return obj

    def set(self, obj: Any, val: Any) -> None:
        """このJSON Pointerに合致するオブジェクトの値を設定する

        Args:
            obj (Any): 走査対象のオブジェクト
            val (Any): 設定する値

        Raises:
            JPtrTypeError: サポートされない型
        """
        lp = len(self.parts)
        if lp == 0:
            obj = val
            return
        if lp > 0:
            p = self.parts[-1]
        if lp > 1:
            obj = JsonPointer.get_obj(obj, self.parts[:-1])
        match obj:
            case MutableMapping():
                obj[p] = val
            case MutableSequence():
                obj[int(p)] = val
            case _:
                raise JPtrTypeError(None, obj)

    @classmethod
    def get_obj(cls, obj: Any, pointer: str | Sequence[str]) -> Any:
        """JSON Pointerに合致するオブジェクトを取得する

        Args:
            obj (Any): 走査対象
            pointer (str | Sequence[str]): JSON Pointer

        Returns:
            Any: 取得したオブジェクト
        """
        ptr = cls(pointer)
        return ptr.get(obj)

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
