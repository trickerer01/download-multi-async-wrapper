# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, ArgumentError
from collections.abc import Sequence
from os import path

from defs import (
    Config, IgnoredArg, CatDwnIds, ExtraArgs, DOWNLOADERS, ACTION_STORE_TRUE, ACTION_APPEND, HELP_DEBUG, HELP_DOWNLOADERS, HELP_CATEGORIES,
    HELP_SCRIPT_PATH, HELP_NO_DOWNLOAD, HELP_NO_UPDATE, HELP_INSTALL, HELP_IGNORE_ARGUMENT, HELP_IDLIST, HELP_APPEND,
)
from logger import trace
from strings import normalize_path, unquote

__all__ = ('parse_arglist', 'valid_dir_path', 'positive_int')


def valid_dir_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(path.expanduser(unquote(pathstr)))
        assert path.isdir(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_file_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(path.expanduser(unquote(pathstr)), False)
        assert path.isfile(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_int(val: str, *, lb: int = None, ub: int = None) -> int:
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
        listed_downloaders = list()
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
        listed_categories = list()
        if len(categories_str) == 0:
            return listed_categories
        lctl = categories_str.split(',')
        for d in lctl:
            assert d not in listed_categories
            listed_categories.append(d)
        return listed_categories
    except Exception:
        raise ArgumentError


def parse_arglist(args: Sequence[str]) -> None:
    parser = ArgumentParser(add_help=False)
    parser.usage = 'main.py -script PATH_TO_FILE [options...]'
    parser.add_argument('--help', action='help', help='Print this message')
    parser.add_argument('--debug', action=ACTION_STORE_TRUE, help=HELP_DEBUG)
    parser.add_argument('--no-download', action=ACTION_STORE_TRUE, help=HELP_NO_DOWNLOAD)
    parser.add_argument('--no-update', action=ACTION_STORE_TRUE, help=HELP_NO_UPDATE)
    parser.add_argument('--install', action=ACTION_STORE_TRUE, help=HELP_INSTALL)
    parser.add_argument('-ignore', metavar='ARG,LEN', default=[], action=ACTION_APPEND, help=HELP_IGNORE_ARGUMENT, type=IgnoredArg)
    parser.add_argument('-idlist', metavar='CAT,DWN,IDS', default=[], action=ACTION_APPEND, help=HELP_IDLIST, type=CatDwnIds)
    parser.add_argument('-append', metavar='CAT,DWN,ARGS', default=[], action=ACTION_APPEND, help=HELP_APPEND, type=ExtraArgs)
    parser.add_argument('-categories', metavar='L,I,S,T', default=[], help=HELP_CATEGORIES, type=valid_categories_list)
    parser.add_argument('-downloaders', metavar='L,I,S,T', default=DOWNLOADERS, help=HELP_DOWNLOADERS, type=valid_downloaders_list)
    parser.add_argument('-script', metavar='PATH_TO_FILE', required=True, help=HELP_SCRIPT_PATH, type=valid_file_path)

    parsed = parser.parse_args(args)
    Config.debug = parsed.debug
    Config.no_download = parsed.no_download
    Config.no_update = parsed.no_update
    Config.install = parsed.install
    Config.ignored_args = parsed.ignore
    Config.override_ids = parsed.idlist
    Config.extra_args = parsed.append
    Config.downloaders = parsed.downloaders
    Config.categories = parsed.categories
    Config.script_path = parsed.script

#
#
#########################################
