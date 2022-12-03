# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, ArgumentError
from os import path
from typing import Optional, List

from defs import (
    HELP_DEBUG, HELP_PATH, HELP_SCRIPT_PATH, HELP_BAK_PATH, HELP_UPDATE, HELP_FETCHER_PATH, HELP_IGNORE_DMODE, ACTION_STORE_TRUE, Config
)
from logger import trace
from strings import normalize_path, unquote

parser = None  # type: Optional[ArgumentParser]


def valid_positive_nonzero_int(val: str) -> int:
    try:
        val = int(val)
        assert(val > 0)
    except Exception:
        raise ArgumentError

    return val


def valid_dir_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr))
        if not path.isdir(newpath):
            raise ValueError
    except Exception:
        raise ArgumentError

    return newpath


def valid_file_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr), False)
        if not path.isfile(newpath):
            raise ValueError
    except Exception:
        raise ArgumentError

    return newpath


def parse_arglist(args: List[str], config=Config) -> None:
    global parser

    parser = ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help')

    parser.add_argument('--debug', action=ACTION_STORE_TRUE, help=HELP_DEBUG)
    parser.add_argument('-path', metavar='#PATH_TO_DIR', default='./', help=HELP_PATH, type=valid_dir_path)
    parser.add_argument('-script', metavar='#PATH_TO_FILE', required=True, help=HELP_SCRIPT_PATH, type=valid_file_path)
    parser.add_argument('--ignore-download-mode', action=ACTION_STORE_TRUE, help=HELP_IGNORE_DMODE)
    parser.add_argument('--update', action=ACTION_STORE_TRUE, help=HELP_UPDATE)
    parser.add_argument('-bakpath', metavar='#PATH_TO_DIR', default='./', help=HELP_BAK_PATH, type=valid_dir_path)
    parser.add_argument('-fetcherpath', metavar='#PATH_TO_DIR', default='./', help=HELP_FETCHER_PATH, type=valid_dir_path)

    try:
        parsed = parser.parse_args(args)
        if parsed.update:
            if parsed.fetcherpath == '':
                trace('-fetcherpath is required!')
                raise ArgumentError
            if parsed.bakpath == '':
                trace('-bakpath is required!')
                raise ArgumentError
        config.debug = parsed.debug
        config.dest_base = parsed.path
        config.script_path = parsed.script
        config.ignore_download_mode = parsed.ignore_download_mode
        config.update = parsed.update
        config.dest_bak_base = parsed.bakpath
        config.fetcher_root = parsed.fetcherpath
    except (ArgumentError, TypeError, ValueError, Exception):
        raise

#
#
#########################################
