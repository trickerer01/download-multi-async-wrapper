# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from locale import getpreferredencoding
from typing import TextIO, Optional

from defs import Wrapper, Config, UTF8
from strings import datetime_str_nfull, timestamped_string

__all__ = ('open_logfile', 'ensure_logfile', 'close_logfile', 'log_to', 'trace')

logfile: Wrapper[Optional[TextIO]] = Wrapper()
buffered_strings = [''] * 0


def open_logfile() -> None:
    title_part = f'{Config.fulltitle}_' if Config.title else ''
    log_basename = f'log_{title_part}{datetime_str_nfull()}.log' if not Config.debug else 'log.log'
    logfile.reset(open(f'{Config.dest_logs_base}{log_basename}', 'at', encoding=UTF8, buffering=1))
    if buffered_strings:
        trace('\n#^^Buffered strings dumped^^#\n', False)


def ensure_logfile() -> None:
    if not logfile:
        open_logfile()


def close_logfile() -> None:
    if logfile:
        trace('\nClosing logfile...\n\n', False)
        logfile().close()
        if Config.test:
            from os import remove
            remove(logfile().name)
        logfile.reset()


def log_to(msg: str, log_file: TextIO, add_timestamp=True) -> None:
    if log_file:
        t_msg = f'{timestamped_string(msg, datetime_str_nfull()) if add_timestamp else msg}\n'
        log_file.write(t_msg)


def trace(msg: str, add_timestamp=True) -> None:
    t_msg = f'{timestamped_string(msg, datetime_str_nfull()) if add_timestamp else msg}\n'
    try:
        if Config.console_log:
            print(t_msg, end='')
    except UnicodeError:
        try:
            print(t_msg.encode(UTF8, errors='backslashreplace').decode(getpreferredencoding(), errors='backslashreplace'), end='')
        except Exception:
            print('<Message was not logged due to UnicodeError>')
    if logfile:
        if buffered_strings:
            for buffered in buffered_strings:
                logfile().write(buffered)
            buffered_strings.clear()
        logfile().write(t_msg)
    else:
        buffered_strings.append(t_msg)

#
#
#########################################
