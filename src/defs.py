# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from abc import ABC, abstractmethod
from os import environ
from typing import List, Union, Tuple, Iterable

IS_IDE = environ.get('PYCHARM_HOSTED') == '1'

UTF8 = 'utf-8'
ACTION_STORE_TRUE = 'store_true'
MIN_IDS_SEQ_LENGTH = 2


class BaseConfig(object):
    def __init__(self) -> None:
        self.debug = False
        self.dest_base = './'
        self.dest_run_base = './'
        self.dest_logs_base = './'
        self.dest_bak_base = './'
        self.script_path = ''
        self.update = False
        self.fetcher_root = ''
        self.ignore_download_mode = False

    def __str__(self) -> str:
        return (
            f'debug: {self.debug}, script: {self.script_path}, dest: {self.dest_base}, run: {self.dest_run_base}, '
            f'logs: {self.dest_logs_base}, bak: {self.dest_bak_base}, update: {self.update}, fetcher: {self.fetcher_root}, '
            f'ignore_download_mode: {self.ignore_download_mode}'
        )

    def __repr__(self) -> str:
        return self.__str__()


Config = BaseConfig()


DOWNLOADER_NM = 'nm'
DOWNLOADER_RV = 'rv'
DOWNLOADER_RN = 'rn'
DOWNLOADER_RX = 'rx'

DOWNLOADERS = [DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RN, DOWNLOADER_RX]

RUXX_INDECIES = [DOWNLOADERS.index(DOWNLOADER_RN), DOWNLOADERS.index(DOWNLOADER_RX)]
RV_INDEX = DOWNLOADERS.index(DOWNLOADER_RV)

HELP_DEBUG = 'Run in debug mode (for development)'
HELP_PATH = 'Path to the folder where all the files / subfolders will be put'
HELP_SCRIPT_PATH = 'Full path to the script (queries) file'
HELP_RUN_PATH = 'Path to the folder where cmd run files will be put if needed'
HELP_LOGS_PATH = 'Path to the folder where logs will be stored'
HELP_BAK_PATH = 'Path to the folder where script backup will be put before updating'
HELP_UPDATE = 'Boolean flag to update script file with current max ids fetched from the websites'
HELP_FETCHER_PATH = 'Path to the folder where max ids fetcher\'s \'main.py\' is located'
HELP_IGNORE_DMODE = 'Boolean flag to ignore all \'-dmode\' arguments and always download files in full'


class Sequence:
    def __init__(self, ids: List[int], line_num: int) -> None:
        self.ids = ids or []  # type: List[int]
        self.line_num = line_num or 0

    def __str__(self) -> str:
        return f'{str(self.ids)} (found and line {self.line_num:d})'

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, item: Union[int, slice]) -> Union[int, List[int]]:
        return self.ids.__getitem__(item)

    def __setitem__(self, key: Union[int, slice], value: Union[int, Iterable[int]]) -> None:
        self.ids.__setitem__(key, value)


class Pair(ABC):
    def __init__(self, vals: Union[list, tuple]) -> None:
        assert len(vals) == 2
        assert isinstance(vals[0], type(vals[1]))

    @abstractmethod
    def __str__(self) -> str:
        ...


class IntPair(Pair):
    def __init__(self, vals: Union[List[int], Tuple[int, int]], *_) -> None:
        super().__init__(vals)
        assert isinstance(vals[0], int)
        self.first = vals[0]  # type: int
        self.second = vals[1]  # type: int

    def __str__(self) -> str:
        return f'first: {self.first:d}, second: {self.second:d}'


class StrPair(Pair):
    def __init__(self, vals: Union[List[str], Tuple[str, str]], *_) -> None:
        super().__init__(vals)
        assert isinstance(vals[0], str)
        self.first = vals[0]  # type: str
        self.second = vals[1]  # type: str

    def __str__(self) -> str:
        return f'first: {self.first}, second: {self.second}'


RANGE_TEMPLATES = {
    DOWNLOADER_NM: StrPair(['-start %d', '-end %d']),
    DOWNLOADER_RV: StrPair(['-start %d', '-end %d']),
    DOWNLOADER_RN: StrPair(['id>=%d', 'id<=%d']),
    DOWNLOADER_RX: StrPair(['id:>=%d', 'id:<=%d']),
}

OS_WINDOWS = 'Windows'
OS_LINUX = 'Linux'
OS_MACOS = 'Darwin'

SUPPORTED_SYSTEMS = [
    OS_WINDOWS,
    OS_LINUX,
    # OS_MACOS,
]

MAX_CMD_LEN = {
    OS_WINDOWS: 32000,
    OS_LINUX: 127000,
    OS_MACOS: 65000,
}


#
#
#########################################
