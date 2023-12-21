# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys

from cmdargs import parse_arglist
from defs import Config, SUPPORTED_SYSTEMS
from executor import execute
from logger import open_logfile, close_logfile, trace
from platform import system as running_system
from queries import read_queries_file, form_queries, update_next_ids
from strings import datetime_str_full
from typing import Sequence

__all__ = ('main_sync',)


def main_sync(args: Sequence[str], config=Config) -> None:
    try:
        parse_arglist(args, config)
        open_logfile(not config.debug, config)
        trace('Logfile opened...', False)
        trace(f'\n# Started at {datetime_str_full()} #')
        read_queries_file(config)
        form_queries(config)
        execute()
        update_next_ids()
        trace(f'\n# Finished at {datetime_str_full()} #')
        trace('\nClosing logfile...\n\n', False)
        close_logfile(config)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(-3)


def run_main() -> None:
    main_sync(sys.argv[1:])


if __name__ == '__main__':
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'
    assert running_system() in SUPPORTED_SYSTEMS
    run_main()
    sys.exit(0)

#
#
#########################################
