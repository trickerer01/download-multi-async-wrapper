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
from config import Config
from defs import MIN_PYTHON_VERSION, MIN_PYTHON_VERSION_STR, SUPPORTED_SYSTEMS
from executor import execute
from logger import close_logfile, trace
from queries import prepare_queries, read_queries_file, update_next_ids
from strings import datetime_str_full

__all__ = ('main_sync',)


def at_startup() -> None:
    if __name__ == '__main__':
        trace(
            f'Python {sys.version}\nCommand-line args: {" ".join(sys.argv)}'
            f'\nEnabled downloaders: "{",".join(Config.downloaders) or "all"}"'
            f'\nEnabled categories: "{",".join(Config.categories) or "all"}"'
            f'\nIgnored arguments: {",".join(str(ign) for ign in Config.ignored_args) or "[]"}'
            f'\nIds overrides: {",".join(str(ove) for ove in Config.override_ids) or "[]"}',
        )


def run_main(args: Sequence[str]) -> int:
    result = 0
    try:
        parse_arglist(args)
        trace('Logfile opened...', False)
        trace(f'\n# Started at {datetime_str_full()} #')
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
