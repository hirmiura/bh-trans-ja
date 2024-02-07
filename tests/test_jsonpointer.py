#!/usr/bin/env -S python
# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
# ruff: noqa: D103
"""JsonPointer周りのテスト"""
from __future__ import annotations

import pytest

import bin.jsonpointer as jp

escape_testdata = [
    ("", ""),
    (" ", " "),
    ("~", "~0"),
    ("/", "~1"),
    ("~/", "~0~1"),
    ("/~", "~1~0"),
]


@pytest.mark.parametrize("input, expected", escape_testdata)
def test_escape(input, expected):
    assert jp.JsonPointer.escape(input) == expected


@pytest.mark.parametrize("expected, input", escape_testdata)
def test_unescape(input, expected):
    assert jp.JsonPointer.unescape(input) == expected


@pytest.mark.parametrize(
    "pointer, expected",
    [
        ("~", jp.JsonPointerError),
        ("~2", jp.JsonPointerError),
        ("~a", jp.JsonPointerError),
        ("~d~", jp.JsonPointerError),
        ("a", jp.JsonPointerError),
        ("a/b", jp.JsonPointerError),
        (3, TypeError),
    ],
)
def test_jsonpointer_new_with_invalid_escape(pointer, expected):
    with pytest.raises(expected):
        jp.JsonPointer(pointer)


@pytest.mark.parametrize(
    "pointer, path, parts",
    [
        ("", "", []),
        ("/ ", "/ ", [" "]),
        ("/a/2/c", "/a/2/c", ["a", "2", "c"]),
        ([], "", []),
        ([" "], "/ ", [" "]),
        (["a", "2", "c"], "/a/2/c", ["a", "2", "c"]),
    ],
)
def test_jsonpointer_new(pointer, path, parts):
    ptr = jp.JsonPointer(pointer)
    assert ptr.path == path
    assert ptr.parts == parts


@pytest.mark.parametrize(
    "path, addition, expected",
    [
        ("", "", ""),
        ("", "/te", "/te"),
        ("/e", "", "/e"),
        ("/a/d", "/3", "/a/d/3"),
        ("/2/r", "/ewr/4/e", "/2/r/ewr/4/e"),
        ("/2/r", "ewr/4/e", "/2/r/ewr/4/e"),
        ("/2/r", ["ewr", "4", "e"], "/2/r/ewr/4/e"),
    ],
)
def test_jsonpointer_join(path, addition, expected):
    ptr = jp.JsonPointer(path)
    new_ptr = ptr.join(addition)
    assert new_ptr.path == expected
    new_ptr = ptr / addition
    assert new_ptr.path == expected
