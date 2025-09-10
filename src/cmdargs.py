# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser
from collections.abc import Sequence

from defs import (
    Config, IgnoredArg, CatDwnIds, ExtraArgs, DOWNLOADERS, ACTION_STORE_TRUE, ACTION_APPEND, HELP_DEBUG, HELP_DOWNLOADERS, HELP_CATEGORIES,
    HELP_SCRIPT_PATH, HELP_NO_DOWNLOAD, HELP_NO_UPDATE, HELP_INSTALL, HELP_IGNORE_ARGUMENT, HELP_IDLIST, HELP_APPEND,
)
from validators import valid_categories_list, valid_downloaders_list, valid_file_path


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
