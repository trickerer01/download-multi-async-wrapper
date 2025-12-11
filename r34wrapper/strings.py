# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import datetime
import pathlib
from collections.abc import Iterable

NEWLINE = '\n'


def unquote(tag: str) -> str:
    return tag.strip('"\'')


def split_into_args(query: str) -> list[str]:
    r"""'a "b c" d "e" f g "{\\"h\\":\\"j\\",\\"k\\":\\"l\\"}"' -> ['a', 'b c', 'd', 'e', 'f', 'g', '{"h":"j","k":"l"}']"""
    def append_result(res_str: str) -> None:
        res_str = unquote(res_str.replace('\\"', '\u2033')).replace('\u2033', '"')
        result.append(res_str)

    result: list[str] = []
    idx1 = idx2 = idxdq = 0
    while idx2 < len(query):
        idx2 += 1
        if idx2 == len(query) - 1:
            result.append(unquote(query[idx1:]))
            break
        if query[idx2] == '"':
            if idx2 == 0 or query[idx2 - 1] != '\\':
                if idxdq != 0:
                    idx2 += 1
                    append_result(query[idxdq:idx2])
                    idxdq = 0
                    idx1 = idx2 + 1
                else:
                    idxdq = idx2
        elif query[idx2] == ' ' and idxdq == 0:
            append_result(query[idx1:idx2])
            idx1 = idx2 + 1
    return result


def first_not_of(string: str, char: str, *, start_idx=0, reverse=False) -> int:
    assert start_idx is None or (0 <= start_idx < len(string))

    if reverse:
        idx = start_idx or len(string)
        while idx >= 0:
            if string[idx] != char:
                return idx
            idx -= 1
    else:
        idx = start_idx or 0
        while 0 <= idx <= len(string) - 1:
            if string[idx] != char:
                return idx
            idx += 1
    return -1


def remove_trailing_comments(line: str) -> str:
    linecopy = line
    idx = linecopy.find(' ##')
    result: str
    if idx == 0:
        result = ''
    elif idx > 0:
        result = linecopy[:first_not_of(linecopy, ' ', start_idx=idx, reverse=True) + 1]
    else:
        result = linecopy
    return result


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


def path_args(dest_base: pathlib.Path, cat: str, sub: str, datepath: bool) -> str:
    date_path = dest_base.joinpath(f'{date_str_md(cat.strip())}') if datepath else dest_base
    sub_path = date_path.joinpath(sub) if sub else date_path
    return f'-path "{sub_path.as_posix()}"'


def time_now_fmt(fmt: str) -> str:
    """datetime.now().strftime() wrapper"""
    return datetime.datetime.now().strftime(fmt)


def datetime_str_full() -> str:
    """
    date in format dd MMM yyyy hh:mm:ss
    usable only for timestamp within log files
    """
    return time_now_fmt('%d %b %Y %H:%M:%S')


def datetime_str_nfull() -> str:
    """
    date in format yyyy-mm-dd_hh_mm_ss
    usable in file names
    """
    return time_now_fmt('%Y-%m-%d_%H_%M_%S')


def date_str_md(cat: str) -> str:
    """
    date in '{cat}_mmdd' format
    usable in folder names
    """
    return f'{f"{cat}_" if cat else ""}{time_now_fmt("%m%d")}'

#
#
#########################################
