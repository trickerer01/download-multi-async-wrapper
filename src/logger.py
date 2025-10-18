# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from locale import getpreferredencoding
from typing import TextIO

from config import Config
from containers import Wrapper
from defs import UTF8
from strings import NEWLINE, datetime_str_nfull, timestamped_string

__all__ = ('close_logfile', 'ensure_logfile', 'log_to', 'trace')

logfile: Wrapper[TextIO] = Wrapper()
buffered_strings: list[str] = []

PREF_ENCODING = getpreferredencoding()
IO_ERR_POLICY = 'backslashreplace'


def _open_logfile() -> None:
    title_part = f'{Config.full_title}_' if Config.title else ''
    log_basename = f'log_{title_part}{datetime_str_nfull()}.log' if not Config.debug else 'log.log'
    logfile.reset(open(f'{Config.dest_logs_base}{log_basename}', 'at', encoding=UTF8, errors=IO_ERR_POLICY, buffering=1))
    if buffered_strings:
        trace('\n#^^Buffered strings dumped^^#\n', False)


def ensure_logfile() -> None:
    if not logfile:
        _open_logfile()


def close_logfile() -> None:
    if logfile:
        trace('\nClosing logfile...\n\n', False)
        logfile.val.close()
        if Config.test:
            import os
            os.remove(logfile.val.name)
        logfile.reset()
    elif buffered_strings:
        trace(f'\nWarning: logfile isn\'t opened, buffered log messages were never dumped! Contents:\n{NEWLINE.join(buffered_strings)}')
        buffered_strings.clear()


def log_to(msg: str, log_file: TextIO, add_timestamp=True) -> None:
    if log_file:
        t_msg = f'{timestamped_string(msg) if add_timestamp else msg}\n'
        log_file.write(t_msg)


def trace(msg: str, add_timestamp=True) -> None:
    t_msg = f'{timestamped_string(msg) if add_timestamp else msg}\n'
    try:
        if Config.console_log:
            print(t_msg, end='')
    except UnicodeError:
        try:
            print(t_msg.encode(UTF8, errors=IO_ERR_POLICY).decode(PREF_ENCODING, errors=IO_ERR_POLICY), end='')
        except Exception:
            print('<Message was not logged due to UnicodeError>')
    if logfile:
        if buffered_strings:
            logfile.val.writelines(buffered_strings)
            buffered_strings.clear()
        logfile.val.write(t_msg)
    else:
        buffered_strings.append(t_msg)

#
#
#########################################
