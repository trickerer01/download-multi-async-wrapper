# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from argparse import ArgumentError

from defs import DOWNLOADERS
from logger import trace
from strings import normalize_path, unquote


def valid_dir_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(os.path.expanduser(unquote(pathstr)))
        assert os.path.isdir(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_file_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(os.path.expanduser(unquote(pathstr)), False)
        assert os.path.isfile(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_int(val: str, *, lb: int | None = None, ub: int | None = None) -> int:
    try:
        val = int(val)
        assert lb is None or val >= lb
        assert ub is None or val <= ub
        return val
    except Exception:
        raise ArgumentError


def positive_int(val: str) -> int:
    return valid_int(val, lb=0)


def valid_downloaders_list(downloaders_str: str) -> list[str]:
    try:
        if len(downloaders_str) == 0:
            trace('Downloaders list can\'t be empty, use --no-download instead!')
            raise ValueError
        listed_downloaders = []
        ldll = [d.lower() for d in downloaders_str.split(',')]
        for d in ldll:
            assert d in DOWNLOADERS
            assert d not in listed_downloaders
            listed_downloaders.append(d)
        listed_downloaders.clear()
        for d in DOWNLOADERS:
            if d in ldll:
                listed_downloaders.append(d)
        return listed_downloaders
    except Exception:
        raise ArgumentError


def valid_categories_list(categories_str: str) -> list[str]:
    try:
        listed_categories = []
        if len(categories_str) == 0:
            return listed_categories
        lctl = categories_str.split(',')
        for d in lctl:
            assert d not in listed_categories
            listed_categories.append(d)
        return listed_categories
    except Exception:
        raise ArgumentError

#
#
#########################################
