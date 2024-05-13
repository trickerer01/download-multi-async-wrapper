# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, ArgumentError
from os import path
from typing import List, Sequence

from defs import (
    Config, DOWNLOADERS, ACTION_STORE_TRUE, HELP_DEBUG, HELP_DOWNLOADERS, HELP_PATH, HELP_SCRIPT_PATH, HELP_RUN_PATH, HELP_LOGS_PATH,
    HELP_BAK_PATH, HELP_UPDATE, HELP_NO_DOWNLOAD, HELP_IGNORE_DMODE,
)
from logger import trace
from strings import normalize_path, unquote

__all__ = ('parse_arglist',)


def valid_dir_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr))
        assert path.isdir(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_file_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr), False)
        assert path.isfile(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_downloaders_list(downloaders_str: str) -> List[str]:
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


def parse_arglist(args: Sequence[str]) -> None:
    ncdir = normalize_path(path.curdir)
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help')
    parser.add_argument('--debug', action=ACTION_STORE_TRUE, help=HELP_DEBUG)
    parser.add_argument('--no-download', action=ACTION_STORE_TRUE, help=HELP_NO_DOWNLOAD)
    parser.add_argument('-downloaders', metavar='#L,I,S,T', default=DOWNLOADERS, help=HELP_DOWNLOADERS, type=valid_downloaders_list)
    parser.add_argument('-path', metavar='#PATH_TO_DIR', default=ncdir, help=HELP_PATH, type=valid_dir_path)
    parser.add_argument('-script', metavar='#PATH_TO_FILE', required=True, help=HELP_SCRIPT_PATH, type=valid_file_path)
    parser.add_argument('--ignore-download-mode', action=ACTION_STORE_TRUE, help=HELP_IGNORE_DMODE)
    parser.add_argument('--update', action=ACTION_STORE_TRUE, help=HELP_UPDATE)
    parser.add_argument('-runpath', metavar='#PATH_TO_DIR', default=ncdir, help=HELP_RUN_PATH, type=valid_dir_path)
    parser.add_argument('-logspath', metavar='#PATH_TO_DIR', default=ncdir, help=HELP_LOGS_PATH, type=valid_dir_path)
    parser.add_argument('-bakpath', metavar='#PATH_TO_DIR', default=ncdir, help=HELP_BAK_PATH, type=valid_dir_path)

    parsed = parser.parse_args(args)
    Config.debug = parsed.debug
    Config.no_download = parsed.no_download
    Config.downloaders = parsed.downloaders
    Config.dest_base = parsed.path
    Config.script_path = parsed.script
    Config.ignore_download_mode = parsed.ignore_download_mode
    Config.update = parsed.update
    Config.dest_run_base = parsed.runpath
    Config.dest_logs_base = parsed.logspath
    Config.dest_bak_base = parsed.bakpath

#
#
#########################################
