# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace

from defs import APPEND_SEPARATOR, IDLIST_SEPARATOR, MAX_CMD_LEN, OS_WINDOWS

__all__ = ('CatDwnIds', 'Config', 'ExtraArgs', 'IgnoredArg')


class IgnoredArg:
    def __init__(self, ignored_fmt: str) -> None:
        try:
            ignored_name, ignored_num = tuple(ignored_fmt.split(',', 1))
            assert ignored_name and ' ' not in ignored_name and ignored_num in ('1', '2')
            self._name = ignored_name
            self._len = int(ignored_num)
        except Exception:
            raise ValueError(f'Invalid ignored arg format: \'{ignored_fmt}\'')

    @property
    def name(self) -> str:
        return self._name

    @property
    def len(self) -> int:
        return self._len

    def __str__(self) -> str:
        return f'{self._name}({self._len:d})'

    __repr__ = __str__


class CatDwnIds:
    def __init__(self, cat_dwn_ids_fmt: str) -> None:
        try:
            cat, dt, ids = tuple(cat_dwn_ids_fmt.split(IDLIST_SEPARATOR, 2))
            idlist = ids.split(IDLIST_SEPARATOR)
            assert cat and dt and idlist
            assert all(int(_) for _ in idlist)
            self._name = f'{cat}:{dt}'
            self._idlist = idlist
        except Exception:
            raise ValueError(f'Invalid ids override format: \'{cat_dwn_ids_fmt}\'')

    @property
    def name(self) -> str:
        return self._name

    @property
    def ids(self) -> list[int]:
        return [int(_) for _ in self._idlist]

    @property
    def len(self) -> int:
        return len(self._idlist)

    def __str__(self) -> str:
        return f'\'{self._name}\': \'{" ".join(self._idlist)}\' ({self.len:d})'

    __repr__ = __str__


class ExtraArgs:
    def __init__(self, cat_dwn_args_fmt: str) -> None:
        try:
            cat, dt, args = tuple(cat_dwn_args_fmt.split(APPEND_SEPARATOR, 2))
            arglist = args.split(APPEND_SEPARATOR)
            assert cat and dt and arglist
            self._name = f'{cat}:{dt}'
            self._arglist = arglist
            self.used = False
        except Exception:
            raise ValueError(f'Invalid extra arg(s) format: \'{cat_dwn_args_fmt}\'')

    @property
    def name(self) -> str:
        return self._name

    @property
    def args(self) -> list[str]:
        return self._arglist.copy()

    @property
    def len(self) -> int:
        return len(self._arglist)

    def __str__(self) -> str:
        return f'\'{self._name}\': \'{" ".join(self._arglist)}\' ({self.len:d})'

    __repr__ = __str__


class BaseConfig:
    DEFAULT_PATH = './'

    def __init__(self, *, test=False, console_log=False) -> None:
        # arguments
        # cmd
        self.debug: bool = False
        self.no_download: bool = False
        self.no_update: bool = False
        self.install: bool = False
        self.ignored_args: list[IgnoredArg] = []
        self.override_ids: list[CatDwnIds] = []
        self.extra_args: list[ExtraArgs] = []
        self.downloaders: tuple[str, ...] = ()
        self.categories: list[str] = []
        self.script_path: str = ''
        # script
        self.dest_base: str = BaseConfig.DEFAULT_PATH
        self.dest_run_base: str = BaseConfig.DEFAULT_PATH
        self.dest_logs_base: str = BaseConfig.DEFAULT_PATH
        self.dest_bak_base: str = BaseConfig.DEFAULT_PATH
        self.title: str = ''
        self.title_increment: int = 0
        self.python: str = ''
        self.datesub: bool = True
        self.update: bool = False
        self.update_offsets: dict[str, int] = {}
        self.noproxy_fetches: set[str] = set()
        # calculated
        self.title_increment_value: str = ''
        self.max_cmd_len: int = MAX_CMD_LEN[OS_WINDOWS] // 2  # MAX_CMD_LEN.get(running_system())
        self.disabled_downloaders: dict[str, set[str]] = {}
        # internal
        self.test: bool = test
        self.console_log: bool = console_log or not test

    def _reset(self) -> None:
        self.__init__(test=self.test, console_log=self.console_log)

    def read(self, params: Namespace) -> None:
        self.debug = params.debug or self.debug
        self.no_download = params.no_download or self.no_download
        self.no_update = params.no_update or self.no_update
        self.install = params.install or self.install
        self.ignored_args = params.ignore or self.ignored_args
        self.override_ids = params.idlist or self.override_ids
        self.extra_args = params.append or self.extra_args
        self.downloaders = params.downloaders or self.downloaders
        self.categories = params.categories or self.categories
        self.script_path = params.script or self.script_path

    @property
    def full_title(self) -> str:
        return f'{self.title}{self.title_increment_value}'

    def __str__(self) -> str:
        return (
            f'debug: {self.debug}, downloaders: {self.downloaders!s}, script: {self.script_path}, dest: {self.dest_base}, '
            f'run: {self.dest_run_base}, logs: {self.dest_logs_base}, bak: {self.dest_bak_base}, update: {self.update}, '
            f'no_download: {self.no_download}, no_update: {self.no_update}, ignored_args: {self.ignored_args!s}, '
            f'id_overrides: {self.override_ids!s}, max_cmd_len: {self.max_cmd_len}'
        )

    __repr__ = __str__


Config: BaseConfig = BaseConfig()

#
#
#########################################
