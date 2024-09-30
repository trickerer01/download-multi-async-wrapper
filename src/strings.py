# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from collections.abc import Iterable
from datetime import datetime

SLASH = '/'
NEWLINE = '\n'


def unquote(tag: str) -> str:
    return tag.strip('"\'')


def normalize_path(basepath: str, append_slash=True) -> str:
    normalized_path = basepath.replace('\\', SLASH)
    need_slash = append_slash is True and len(normalized_path) != 0 and normalized_path[-1] != SLASH
    return f'{normalized_path}{SLASH}' if need_slash else normalized_path


def timestamped_string(msg: str) -> str:
    ts = f'[{datetime_str_nfull()}] '
    nts = f'{NEWLINE}{ts}'
    return msg.replace(NEWLINE, nts) if msg.startswith(NEWLINE) else f'{ts}{msg.replace(NEWLINE, nts)}'


def all_tags_same_sign(taglist: Iterable[str], negative: bool) -> bool:
    all_same_sign = True
    for tag in taglist:
        all_same_sign = all_same_sign and (tag.startswith('-') is negative)
    return all_same_sign


def all_tags_negative(taglist: Iterable[str]) -> bool:
    return all_tags_same_sign(taglist, True)


def all_tags_positive(taglist: Iterable[str]) -> bool:
    return all_tags_same_sign(taglist, False)


def path_args(dest_base: str, cat: str, sub: str, datepath: bool) -> str:
    return f'-path "{dest_base}{f"{date_str_md(cat.strip())}/" if datepath else ""}{f"{sub}/" if sub else ""}"'


def time_now_fmt(fmt: str) -> str:
    """datetime.now().strftime() wrapper"""
    return datetime.now().strftime(fmt)


def datetime_str_full() -> str:
    """
    date in format dd MMM yyyy hh:mm:ss\n\n
    usable only for timestamp within log files
    """
    return time_now_fmt('%d %b %Y %H:%M:%S')


def datetime_str_nfull() -> str:
    """
    date in format yyyy-mm-dd_hh_mm_ss\n\n
    usable in file names
    """
    return time_now_fmt('%Y-%m-%d_%H_%M_%S')


def date_str_md(cat: str) -> str:
    """
    date in '{cat}_mmdd' format\n\n
    usable in folder names
    """
    return f'{f"{cat}_" if cat else ""}{time_now_fmt("%m%d")}'

#
#
#########################################
