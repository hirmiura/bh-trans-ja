#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
"""オブジェクトを走査する"""

from __future__ import annotations

import sys
from typing import Any, NamedTuple

from jsonpointer import JsonPointer

type TypeListT = tuple[type, ...]  # type: ignore
type ObjectListT = tuple[Any, ...]  # type: ignore


class WalkedPath(NamedTuple):
    """walkで使用するデータクラス"""

    pointer: JsonPointer
    types: TypeListT
    objects: ObjectListT


def update_type(wpath: WalkedPath, ty: type) -> WalkedPath:
    """タイプリストの末尾を変更する

    Args:
        wpath (WalkedPath): 対象のパスオブジェクト
        ty (type): 変更後の型

    Returns:
        WalkedPath: 変更された新しいパスオブジェクト
    """
    return WalkedPath(wpath.pointer, wpath.types[:-1] + (ty,), wpath.objects)


def child_walk(child: Any, wpath: WalkedPath, key: str) -> list[WalkedPath]:
    """子オブジェクトを走査する

    Args:
        child (Any): 子オブジェクト
        wpath (WalkedPath): 親パス
        key (str): キー名

    Returns:
        list[WalkedPath]: _description_
    """
    child_path = wpath.pointer / (key,)
    child_types = wpath.types + (type(child),)
    child_objects = wpath.objects + (child,)
    return walk(child, WalkedPath(child_path, child_types, child_objects))


def walk(obj: Any, wpath: WalkedPath | None = None) -> list[WalkedPath]:
    """オブジェクトを走査する

    Args:
        obj (Any): オブジェクト
        wpath (WalkedPath | None, optional): パスオブジェクト. Defaults to None.

    Raises:
        TypeError: 未サポート型がある

    Returns:
        list[WalkedPath]: パスオブジェクトのリスト
    """
    # wpathが空であればルートとみなす
    if not wpath:
        wpath = WalkedPath(JsonPointer(""), (type(None),), (obj,))

    result: list[WalkedPath] = []
    match obj:
        case dict():
            wpath = update_type(wpath, dict)
            for k, child in obj.items():
                children = child_walk(child, wpath, str(k))
                result.extend(children)
        case list():
            wpath = update_type(wpath, list)
            for i, child in enumerate(obj):
                children = child_walk(child, wpath, str(i))
                result.extend(children)
        case str():
            wpath = update_type(wpath, str)
            result.append(wpath)
        case int():
            wpath = update_type(wpath, int)
            result.append(wpath)
        case float():
            wpath = update_type(wpath, float)
            result.append(wpath)
        case bool():
            wpath = update_type(wpath, bool)
            result.append(wpath)
        case None:
            wpath = update_type(wpath, type(None))
            result.append(wpath)
        case _:
            raise TypeError(f"サポートされない型です。type: {type(obj)}")

    return result


def main() -> int:
    """メイン関数

    Returns:
        int: 成功時は0を返す
    """
    tests = walk({"top1": {"id": "test1", "li st1": [0, 1, {"in.list": None}, 3]}, "top2": {}})
    for t in tests:
        print(t.pointer)
        print(", ".join(t.__name__ for t in t.types))
        print("\n".join(str(o) for o in t.objects))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
