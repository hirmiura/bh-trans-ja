#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""JSON Pointer Exceptionを定義する"""

from __future__ import annotations


class JPtrException(Exception):  # noqa: N818
    """JsonPointer関連で発生する例外を表すクラス"""

    def __init__(self, *args):
        """JsonPointer関連で発生する例外を表す"""
        super().__init__(*args)


class JPtrInvalidEscapeError(JPtrException):
    """JsonPointer関連で発生した不正なエスケープ例外を表すクラス"""

    def __init__(self, message: str | None = None, *args):
        """JsonPointer関連で発生した不正なエスケープ例外を表す

        Args:
            message (str | None, optional): メッセージ。デフォルト: None.
            *args: 任意の引数
        """
        message = message or "不正なエスケープを含んでいます"
        super().__init__(message, *args)


class JPtrNotSlashStartError(JPtrException):
    """JsonPointer関連で発生した非スラッシュ開始例外を表すクラス"""

    def __init__(self, message: str | None = None, *args):
        """JsonPointer関連で発生した非スラッシュ開始例外を表す

        Args:
            message (str | None, optional):メッセージ。デフォルト: None.
            *args: 任意の引数
        """
        message = message or "ポインタは「/」で開始しなければなりません"
        super().__init__(message, *args)


class JPtrTypeError(TypeError, JPtrException):
    """JsonPointer関連で発生したTypeError例外を表すクラス"""

    def __init__(self, message: str | None = None, *args):
        """JsonPointer関連で発生したTypeError例外を表す

        Args:
            message (str | None, optional):メッセージ。デフォルト: None.
            *args: 任意の引数
        """
        message = message or "サポートされない型です"
        super().__init__(message, *args)
