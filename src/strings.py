# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from datetime import datetime
from typing import List

SLASH = '/'
NEWLINE = '\n'


def unquote(tag: str) -> str:
    while len(tag) > 1 and tag[0] == tag[-1] and tag[0] in ['"', '\'']:
        tag = tag[1:-1]
    return tag


def normalize_path(basepath: str, append_slash: bool = True) -> str:
    normalized_path = basepath.replace('\\', SLASH)
    if append_slash and len(normalized_path) != 0 and normalized_path[-1] != SLASH:
        normalized_path += SLASH
    return normalized_path


def timestamped_string(msg: str, timestamp: str) -> str:
    return msg.replace('\n', f'\n[{timestamp}] ') if msg[0] == '\n' else (f'[{timestamp}] ' + msg.replace('\n', f'\n[{timestamp}] '))


def all_tags_negative(taglist: List[str]) -> bool:
    all_neg = True
    for tag in taglist:
        all_neg &= tag[0] == '-'
    return all_neg


def normalize_ruxx_tag(tag: str) -> str:
    tag = tag.replace('+', '%2b')
    if tag[0] == '(' and tag[-1] == ')' and tag.find('~') != -1:
        tag = f'(+{"+~+".join(part for part in tag[1:-1].split("~"))}+)'
    return tag


def path_args(dest_base: str, img: bool, sub: str) -> str:
    return f'-path "{dest_base}{date_str_md(img)}/{sub}{"/" if len(sub) > 0 else ""}"'


def bytes_to_lines(raw: bytes) -> List[str]:
    return raw.decode().replace('\r\n', '\n').split('\n')


def time_now_fmt(fmt: str) -> str:
    """
    datetime.now().strftime() wrapper
    """
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


def date_str_md(img: bool) -> str:
    """
    date in format:\n\n
    'mmdd' for videos\n\n
    'img_mmdd' for images\n\n
    usable in folder names
    """
    return f'{"img_" if img else ""}{datetime.today().strftime("%m%d")}'

#
#
#########################################
