# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from collections.abc import Sequence
from platform import system as running_system

from cmdargs import parse_arglist
from defs import SUPPORTED_SYSTEMS, MIN_PYTHON_VERSION, MIN_PYTHON_VERSION_STR
from executor import execute
from logger import close_logfile, trace
from queries import read_queries_file, prepare_queries, update_next_ids, at_startup
from strings import datetime_str_full

__all__ = ('main_sync',)


def run_main(args: Sequence[str]) -> int:
    result = 0
    try:
        parse_arglist(args)
        trace('Logfile opened...', False)
        trace(f'\n# Started at {datetime_str_full()} #')
        if __name__ == '__main__':
            at_startup()
        read_queries_file()
        prepare_queries()
        execute()
        update_next_ids()
        trace(f'\n# Finished at {datetime_str_full()} #')
    except KeyboardInterrupt:
        trace('Warning: catched KeyboardInterrupt...')
        result = -4
    except Exception:
        import traceback
        traceback.print_exc()
        result = -3
    finally:
        close_logfile()
        return result


def main_sync(args: Sequence[str]) -> int:
    assert sys.version_info >= MIN_PYTHON_VERSION, f'Minimum python version required is {MIN_PYTHON_VERSION_STR}!'
    assert running_system() in SUPPORTED_SYSTEMS, f'Unsupported system \'{running_system()}\''
    return run_main(args)


if __name__ == '__main__':
    sys.exit(main_sync(sys.argv[1:]))

#
#
#########################################
