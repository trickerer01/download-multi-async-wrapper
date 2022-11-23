# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys

from cmdargs import parse_arglist
from executor import execute
from logger import open_logfile, close_logfile, trace
from queries import read_queries_file, form_queries, update_next_ids
from strings import datetime_str_full


def cleanup() -> None:
    pass


def run_main() -> None:
    try:
        open_logfile()
        trace('Logfile opened...', False)
        parse_arglist(sys.argv[1:])
        trace(f'\n# Started at {datetime_str_full()} #')
        read_queries_file()
        form_queries()
        execute()
        update_next_ids()
        cleanup()
        trace(f'\n# Finished at {datetime_str_full()} #')
        trace('\nClosing logfile...\n\n', False)
        close_logfile()
    except Exception:
        trace(f'\nFailure! Exited with exception:\n{str(sys.exc_info()[0])}: {str(sys.exc_info()[1])}\n')
        sys.exit(-3)


if __name__ == '__main__':
    run_main()
    sys.exit(0)

#
#
#########################################
