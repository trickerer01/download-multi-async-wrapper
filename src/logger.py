# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from locale import getpreferredencoding
from typing import TextIO, Optional

from defs import UTF8, Config
from strings import datetime_str_nfull, timestamped_string

logfile = None  # type: Optional[TextIO]


def get_logfile() -> TextIO:
    assert logfile, 'No logfile present, get_logfile() call is illegal'
    return logfile


def open_logfile(timestamped=True) -> None:
    global logfile
    log_basename = f'log_{datetime_str_nfull()}.log' if timestamped else 'log.log'
    logfile = open(f'{Config.dest_logs_base}{log_basename}', 'at', encoding=UTF8, buffering=True)


def close_logfile() -> None:
    global logfile
    if logfile:
        logfile.close()
        logfile = None


def log_to(msg: str, log_file: TextIO, add_timestamp=True) -> None:
    if log_file:
        t_msg = f'{timestamped_string(msg, datetime_str_nfull()) if add_timestamp else msg}\n'
        log_file.write(t_msg)


def trace(msg: str, add_timestamp=True) -> None:
    t_msg = f'{timestamped_string(msg, datetime_str_nfull()) if add_timestamp else msg}\n'
    try:
        print(t_msg, end='')
    except UnicodeError:
        print(f'message was: {bytearray(map(ord, t_msg))}')
        try:
            print(t_msg.encode(UTF8).decode(), end='')
        except Exception:
            try:
                print(t_msg.encode(UTF8).decode(getpreferredencoding()), end='')
            except Exception:
                print('<Message was not logged due to UnicodeError>')
        finally:
            print('Previous message caused UnicodeError...')
    if logfile:
        logfile.write(t_msg)

#
#
#########################################
