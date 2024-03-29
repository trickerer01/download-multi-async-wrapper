# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from abc import ABC, abstractmethod
from typing import List, Union, Tuple, Iterable, TypeVar

UTF8 = 'utf-8'
ACTION_STORE_TRUE = 'store_true'
PROXY_ARG = '-proxy'
MIN_IDS_SEQ_LENGTH = 2

OS_WINDOWS = 'Windows'
OS_LINUX = 'Linux'
OS_MACOS = 'Darwin'

SUPPORTED_SYSTEMS = (
    OS_WINDOWS,
    OS_LINUX,
    # OS_MACOS,
)

MAX_CMD_LEN = {
    OS_WINDOWS: 32000,
    OS_LINUX: 127000,
    OS_MACOS: 65000,
}

DOWNLOADER_NM = 'nm'
DOWNLOADER_RV = 'rv'
DOWNLOADER_RN = 'rn'
DOWNLOADER_RX = 'rx'
DOWNLOADER_RS = 'rs'

DOWNLOADERS = [DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS]
RUXX_DOWNLOADERS = (DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS)
RUN_FILE_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV)

APP_NAME_NM = DOWNLOADER_NM.upper(),
APP_NAME_RV = DOWNLOADER_RV.upper(),
APP_NAME_RUXX = 'Ruxx'
APP_NAMES = {
    DOWNLOADER_NM: APP_NAME_NM,
    DOWNLOADER_RV: APP_NAME_RV,
    DOWNLOADER_RN: APP_NAME_RUXX,
    DOWNLOADER_RX: APP_NAME_RUXX,
    DOWNLOADER_RS: APP_NAME_RUXX,
}


class BaseConfig(object):
    def __init__(self, *, test=False, console_log=False) -> None:
        # arguments
        self.debug = False
        self.downloaders = list()  # type: List[str]
        self.dest_base = './'
        self.dest_run_base = './'
        self.dest_logs_base = './'
        self.dest_bak_base = './'
        self.script_path = ''
        self.update = False
        self.no_download = False
        self.ignore_download_mode = False
        # calculated
        self.max_cmd_len = MAX_CMD_LEN[OS_WINDOWS] // 2  # MAX_CMD_LEN.get(running_system())
        self.python = ''
        # non-cmd params
        self.test = test
        self.console_log = not (test and not console_log)

    def _reset(self) -> None:
        self.__init__(test=self.test, console_log=self.console_log)

    def __str__(self) -> str:
        return (
            f'debug: {self.debug}, downloaders: {str(self.downloaders)}, script: {self.script_path}, dest: {self.dest_base}, '
            f'run: {self.dest_run_base}, logs: {self.dest_logs_base}, bak: {self.dest_bak_base}, update: {self.update}, '
            f'no_download: {self.no_download}, ignore_download_mode: {self.ignore_download_mode}, '
            f'max_cmd_len: {self.max_cmd_len}'
        )

    __repr__ = __str__


Config = BaseConfig()

HELP_DEBUG = 'Run in debug mode (for development)'
HELP_DOWNLOADERS = f'Enabled downloaders. Default is all: \'{",".join(DOWNLOADERS)}\''
HELP_PATH = 'Path to the folder where all the files / subfolders will be put'
HELP_SCRIPT_PATH = 'Full path to the script (queries) file'
HELP_RUN_PATH = 'Path to the folder where cmd run files will be put if needed'
HELP_LOGS_PATH = 'Path to the folder where logs will be stored'
HELP_BAK_PATH = 'Path to the folder where script backup will be put before updating'
HELP_UPDATE = 'Boolean flag to update script file with current max ids fetched from the websites'
HELP_NO_DOWNLOAD = 'Boolean flag to skip actual download (do not launch downloaders)'
HELP_IGNORE_DMODE = 'Boolean flag to ignore all \'-dmode\' arguments and always download files in full'

PATH_APPEND_DOWNLOAD_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_DOWNLOAD_NM = 'src/ids.py'
PATH_APPEND_DOWNLOAD_RV = PATH_APPEND_DOWNLOAD_NM

PATH_APPEND_UPDATE_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_UPDATE_NM = 'src/pages.py'
PATH_APPEND_UPDATE_RV = PATH_APPEND_UPDATE_NM

PATH_APPEND_DOWNLOAD = {
    DOWNLOADER_NM: PATH_APPEND_DOWNLOAD_NM,
    DOWNLOADER_RV: PATH_APPEND_DOWNLOAD_RV,
    DOWNLOADER_RN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RX: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RS: PATH_APPEND_DOWNLOAD_RUXX,
}

PATH_APPEND_UPDATE = {
    DOWNLOADER_NM: PATH_APPEND_UPDATE_NM,
    DOWNLOADER_RV: PATH_APPEND_UPDATE_RV,
    DOWNLOADER_RN: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RX: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RS: PATH_APPEND_UPDATE_RUXX,
}


class IntSequence:
    def __init__(self, ids: Iterable[int], line_num: int) -> None:
        self.ids = list(ids or [])
        self.line_num = line_num or 0

    def __str__(self) -> str:
        return f'{str(self.ids)} (found at line {self.line_num:d})'

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, item: Union[int, slice]) -> Union[int, List[int]]:
        return self.ids.__getitem__(item)

    def __setitem__(self, key: Union[int, slice], value: Union[int, Iterable[int]]) -> None:
        self.ids.__setitem__(key, value)


class Pair(ABC):
    PT = TypeVar('PT')

    @abstractmethod
    def __init__(self, vals: Tuple[PT, PT]) -> None:
        self._first, self._second = vals
        self._fmt = {int: 'd', bool: 'd', float: '.2f', oct: 'o'}.get(type(self._first), '')

    @property
    def first(self) -> PT:
        return self._first

    @property
    def second(self) -> PT:
        return self._second

    def __str__(self) -> str:
        return f'first: {self._first:{self._fmt}}, second: {self._second:{self._fmt}}'

    __repr__ = __str__


class IntPair(Pair):
    def __init__(self, vals: Tuple[int, int]) -> None:
        super().__init__(vals)


class StrPair(Pair):
    def __init__(self, vals: Tuple[str, str]) -> None:
        super().__init__(vals)


RANGE_TEMPLATES = {
    DOWNLOADER_NM: StrPair(('-start %d', '-end %d')),
    DOWNLOADER_RV: StrPair(('-start %d', '-end %d')),
    DOWNLOADER_RN: StrPair(('id>=%d', 'id<=%d')),
    DOWNLOADER_RX: StrPair(('id:>=%d', 'id:<=%d')),
    DOWNLOADER_RS: StrPair(('id:>=%d', 'id:<=%d')),
}

#
#
#########################################
