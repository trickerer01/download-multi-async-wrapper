# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from collections.abc import Iterable
from typing import NamedTuple, TypeVar

UTF8 = 'utf-8'
ACTION_STORE_TRUE = 'store_true'
ACTION_APPEND = 'append'
PROXY_ARG = '-proxy'
MIN_IDS_SEQ_LENGTH = 2
MAX_CATEGORY_NAME_LENGTH = 10

MIN_PYTHON_VERSION = (3, 10)
MIN_PYTHON_VERSION_STR = f'{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}'


# Types
class IntSequence:
    def __init__(self, ints: Iterable[int], line_num: int) -> None:
        self.ints = list(ints or [])
        self.line_num = line_num or -1

    def __str__(self) -> str:
        return f'{self.ints!s} (found at line {self.line_num:d})'

    def __len__(self) -> int:
        return len(self.ints)

    def __getitem__(self, item: int | slice) -> int | list[int]:
        return self.ints.__getitem__(item)

    def __setitem__(self, key: int | slice, value: int | Iterable[int]) -> None:
        self.ints.__setitem__(key, value)

    __repr__ = __str__


class IntPair(NamedTuple):
    first: int
    second: int


class StrPair(NamedTuple):
    first: str
    second: str


DT = TypeVar('DT', str, list, IntSequence)
'''Must have __len__() defined'''
AT = TypeVar('AT')
'''Any type'''
for _ in DT.__constraints__:
    assert hasattr(_, '__len__') and callable(_.__len__), f'DT class \'{_.__name__}\' doesn\'t have len() method!'
# ^ Types ^

OS_WINDOWS = 'Windows'
OS_LINUX = 'Linux'
OS_MACOS = 'Darwin'

SUPPORTED_SYSTEMS = (
    OS_WINDOWS,
    OS_LINUX,
    # OS_MACOS,
)

MAX_CMD_LEN: dict[str, int] = {
    OS_WINDOWS: 32000,
    OS_LINUX: 127000,
    OS_MACOS: 65000,
}

BOOL_STRS: dict[str, bool] = (dict(zip(
    ('YES', 'Yes', 'yes', 'TRUE', 'True', 'true', '1', 'Y', 'y', 'NO', 'No', 'no', 'FALSE', 'False', 'false', '0', 'N', 'n'),
    (True,) * 9 + (False,) * 9,
    strict=True,
)))

DOWNLOADER_NM = 'nm'
DOWNLOADER_RV = 'rv'
DOWNLOADER_RC = 'rc'
DOWNLOADER_RG = 'rg'
DOWNLOADER_RN = 'rn'
DOWNLOADER_RX = 'rx'
DOWNLOADER_RS = 'rs'
DOWNLOADER_RP = 'rp'
DOWNLOADER_EN = 'en'
DOWNLOADER_XB = 'xb'
DOWNLOADER_BB = 'bb'

DOWNLOADERS = [
    DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RG, DOWNLOADER_RN,
    DOWNLOADER_RX, DOWNLOADER_RS, DOWNLOADER_RP, DOWNLOADER_EN, DOWNLOADER_XB, DOWNLOADER_BB,
]
RUXX_DOWNLOADERS = (DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS, DOWNLOADER_RP, DOWNLOADER_EN, DOWNLOADER_XB, DOWNLOADER_BB)
RUN_FILE_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RG)
PAGE_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RG)
COLOR_LOG_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RG)

APP_NAME_NM = DOWNLOADER_NM.upper()
APP_NAME_RV = DOWNLOADER_RV.upper()
APP_NAME_RC = DOWNLOADER_RC.upper()
APP_NAME_RG = DOWNLOADER_RG.upper()
APP_NAME_RUXX = 'Ruxx'

APP_NAMES: dict[str, str] = {
    DOWNLOADER_NM: APP_NAME_NM,
    DOWNLOADER_RV: APP_NAME_RV,
    DOWNLOADER_RC: APP_NAME_RC,
    DOWNLOADER_RG: APP_NAME_RG,
    DOWNLOADER_RN: APP_NAME_RUXX,
    DOWNLOADER_RX: APP_NAME_RUXX,
    DOWNLOADER_RS: APP_NAME_RUXX,
    DOWNLOADER_RP: APP_NAME_RUXX,
    DOWNLOADER_EN: APP_NAME_RUXX,
    DOWNLOADER_XB: APP_NAME_RUXX,
    DOWNLOADER_BB: APP_NAME_RUXX,
}

PATH_APPEND_DOWNLOAD_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_DOWNLOAD_NRVCG_IDS = 'src/ids.py'
PATH_APPEND_DOWNLOAD_NRVCG_PAGES = 'src/pages.py'
PATH_APPEND_UPDATE_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_UPDATE_NRVCG = 'src/pages.py'
PATH_APPEND_REQUIREMENTS = 'requirements.txt'

PATH_APPEND_DOWNLOAD_IDS: dict[str, str] = {
    DOWNLOADER_NM: PATH_APPEND_DOWNLOAD_NRVCG_IDS,
    DOWNLOADER_RV: PATH_APPEND_DOWNLOAD_NRVCG_IDS,
    DOWNLOADER_RC: PATH_APPEND_DOWNLOAD_NRVCG_IDS,
    DOWNLOADER_RG: PATH_APPEND_DOWNLOAD_NRVCG_IDS,
    DOWNLOADER_RN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RX: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RS: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RP: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_EN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_XB: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_BB: PATH_APPEND_DOWNLOAD_RUXX,
}
PATH_APPEND_DOWNLOAD_PAGES: dict[str, str] = {
    DOWNLOADER_NM: PATH_APPEND_DOWNLOAD_NRVCG_PAGES,
    DOWNLOADER_RV: PATH_APPEND_DOWNLOAD_NRVCG_PAGES,
    DOWNLOADER_RC: PATH_APPEND_DOWNLOAD_NRVCG_PAGES,
    DOWNLOADER_RG: PATH_APPEND_DOWNLOAD_NRVCG_PAGES,
    DOWNLOADER_RN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RX: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RS: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RP: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_EN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_XB: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_BB: PATH_APPEND_DOWNLOAD_RUXX,
}

PATH_APPEND_UPDATE: dict[str, str] = {
    DOWNLOADER_NM: PATH_APPEND_UPDATE_NRVCG,
    DOWNLOADER_RV: PATH_APPEND_UPDATE_NRVCG,
    DOWNLOADER_RC: PATH_APPEND_UPDATE_NRVCG,
    DOWNLOADER_RG: PATH_APPEND_UPDATE_NRVCG,
    DOWNLOADER_RN: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RX: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RS: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RP: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_EN: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_XB: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_BB: PATH_APPEND_UPDATE_RUXX,
}

RANGE_ID_TEMPLATE_NRVCG = StrPair('-start %d', ' -end %d')
RANGE_ID_TEMPLATE_RN_RP = StrPair('id>=%d', ' id<=%d')
RANGE_ID_TEMPLATE_RX_RS_XB_BB = StrPair('id:>=%d', ' id:<=%d')
RANGE_ID_TEMPLATE_EN = StrPair('id:%d..', '%d')
RANGE_PAGE_TEMPLATE_NRVCG = StrPair('-pages %d', ' -start %d')
RANGE_PAGE_IDS_TEMPLATE_NRVCG = StrPair('-stop_id %d', '-begin_id %d')

RANGE_TEMPLATE_IDS: dict[str, StrPair] = {
    DOWNLOADER_NM: RANGE_ID_TEMPLATE_NRVCG,
    DOWNLOADER_RV: RANGE_ID_TEMPLATE_NRVCG,
    DOWNLOADER_RC: RANGE_ID_TEMPLATE_NRVCG,
    DOWNLOADER_RG: RANGE_ID_TEMPLATE_NRVCG,
    DOWNLOADER_RN: RANGE_ID_TEMPLATE_RN_RP,
    DOWNLOADER_RX: RANGE_ID_TEMPLATE_RX_RS_XB_BB,
    DOWNLOADER_RS: RANGE_ID_TEMPLATE_RX_RS_XB_BB,
    DOWNLOADER_RP: RANGE_ID_TEMPLATE_RN_RP,
    DOWNLOADER_EN: RANGE_ID_TEMPLATE_EN,
    DOWNLOADER_XB: RANGE_ID_TEMPLATE_RX_RS_XB_BB,
    DOWNLOADER_BB: RANGE_ID_TEMPLATE_RX_RS_XB_BB,
}
RANGE_TEMPLATE_PAGES: dict[str, StrPair] = {
    DOWNLOADER_NM: RANGE_PAGE_TEMPLATE_NRVCG,
    DOWNLOADER_RV: RANGE_PAGE_TEMPLATE_NRVCG,
    DOWNLOADER_RC: RANGE_PAGE_TEMPLATE_NRVCG,
    DOWNLOADER_RG: RANGE_PAGE_TEMPLATE_NRVCG,
}
RANGE_TEMPLATE_PAGE_IDS: dict[str, StrPair] = {
    DOWNLOADER_NM: RANGE_PAGE_IDS_TEMPLATE_NRVCG,
    DOWNLOADER_RV: RANGE_PAGE_IDS_TEMPLATE_NRVCG,
    DOWNLOADER_RC: RANGE_PAGE_IDS_TEMPLATE_NRVCG,
    DOWNLOADER_RG: RANGE_PAGE_IDS_TEMPLATE_NRVCG,
}

HELP_DEBUG = 'Run in debug mode (for development)'
HELP_DOWNLOADERS = f'Enabled downloaders. Default is all: \'{",".join(DOWNLOADERS)}\''
HELP_CATEGORIES = 'Enabled categories. Default is all'
HELP_NO_DOWNLOAD = 'Boolean flag to skip actual download (do not launch downloaders)'
HELP_NO_UPDATE = 'Boolean flag to skip script ids update regardless of script update flag being set or not'
HELP_INSTALL = 'Force install dependencies from enabled downloaders to a Python environment set within the script'
HELP_SCRIPT_PATH = 'Full path to the script (queries) file'
HELP_IGNORE_ARGUMENT = (
    'Script one-line cmd argument to ignore, format: \'<NAME>,<COUNT>\''
    ' where <NAME> is argument name (dash prefix must be omitted) and <COUNT> is a number of arguments to skip (1 or 2).'
    ' Skips the entire line! Can be used multiple times'
)
HELP_IDLIST = (
    'Override id range script parameter for a given \'catergory:downloader\' combination.'
    ' Example: \'vid,rx,50000 51000\' forces RX downloader to use 50000-51000 as ids range when processing \'vid\' category.'
    ' Can be used multiple times'
)
HELP_APPEND = (
    'Append extra argument(s) to a given \'catergory:downloader\' combination cmdline.'
    ' Can be used to override existing identical downloader arguments:'
    ' \'--dest "./" --dest "../"\' will result in the latter value being used once parsed by the downloader.'
    ' Can be used multiple times'
)

#
#
#########################################
