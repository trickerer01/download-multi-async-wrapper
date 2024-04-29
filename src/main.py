# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from platform import system as running_system
from typing import Sequence

from cmdargs import parse_arglist
from defs import SUPPORTED_SYSTEMS
from executor import execute
from logger import open_logfile, close_logfile, trace
from queries import read_queries_file, prepare_queries, update_next_ids
from strings import datetime_str_full

__all__ = ('main_sync',)


def run_main(args: Sequence[str]) -> int:
    result = 0
    try:
        parse_arglist(args)
        open_logfile()
        trace('Logfile opened...', False)
        trace(f'\n# Started at {datetime_str_full()} #')
        read_queries_file()
        prepare_queries()
        execute()
        update_next_ids()
        trace(f'\n# Finished at {datetime_str_full()} #')
    except Exception:
        import traceback
        traceback.print_exc()
        result = -3
    finally:
        trace('\nClosing logfile...\n\n', False)
        close_logfile()
        return result


def main_sync(args: Sequence[str]) -> int:
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'
    assert running_system() in SUPPORTED_SYSTEMS, f'Unsupported system \'{running_system()}\''
    return run_main(args)


if __name__ == '__main__':
    sys.exit(main_sync(sys.argv[1:]))

#
#
#########################################
