# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
# PROJECT-LEVEL IMPORTS ARE RESTRICTED
#

from abc import ABC, abstractmethod
from typing import List, Union, Tuple, Iterable, Type, TypeVar, Dict, Optional, Any, Generic, Set

UTF8 = 'utf-8'
ACTION_STORE_TRUE = 'store_true'
ACTION_APPEND = 'append'
PROXY_ARG = '-proxy'
MIN_IDS_SEQ_LENGTH = 2
MAX_CATEGORY_NAME_LENGTH = 10

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

BOOL_STRS: Dict[str, bool] = ({y: v for y, v in zip(
    ('YES', 'Yes', 'yes', 'TRUE', 'True', 'true', '1', 'Y', 'y', 'NO', 'No', 'no', 'FALSE', 'False', 'false', '0', 'N', 'n'),
    (True,) * 9 + (False,) * 9
)})


def unused_argument(arg: Any) -> None:
    bool(arg)


def assert_notnull(obj: Any) -> Any:
    assert obj is not None
    return obj


class IntSequence:
    def __init__(self, ints: Iterable[int], line_num: int) -> None:
        self.ints = list(ints or [])
        self.line_num = line_num or -1

    def __str__(self) -> str:
        return f'{str(self.ints)} (found at line {self.line_num:d})'

    def __len__(self) -> int:
        return len(self.ints)

    def __getitem__(self, item: Union[int, slice]) -> Union[int, List[int]]:
        return self.ints.__getitem__(item)

    def __setitem__(self, key: Union[int, slice], value: Union[int, Iterable[int]]) -> None:
        self.ints.__setitem__(key, value)

    __repr__ = __str__


class Pair(ABC):
    PT = TypeVar('PT')

    @abstractmethod
    def __init__(self, vals: Tuple[PT, PT]) -> None:
        self._first, self._second = vals
        self._fmt = {int: 'd', bool: 'd', float: '.2f'}.get(type(self._first), '')

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


class IgnoredArg:
    def __init__(self, ignored_fmt: str) -> None:
        try:
            ignored_name, ignored_num = tuple(ignored_fmt.split(',', 1))
            assert ignored_name and ' ' not in ignored_name and int(ignored_num) in (1, 2)
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
            cat, dt, ids = tuple(cat_dwn_ids_fmt.split(',', 2))
            idlist = ids.split(' ')
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
    def ids(self) -> List[int]:
        return [int(_) for _ in self._idlist]

    @property
    def len(self) -> int:
        return len(self._idlist)

    def __str__(self) -> str:
        return f'\'{self._name}\': \'{" ".join(self._idlist)}\' ({self.len:d})'

    __repr__ = __str__


DOWNLOADER_NM = 'nm'
DOWNLOADER_RV = 'rv'
DOWNLOADER_RC = 'rc'
DOWNLOADER_RN = 'rn'
DOWNLOADER_RX = 'rx'
DOWNLOADER_RS = 'rs'
DOWNLOADER_RZ = 'rz'
DOWNLOADER_RP = 'rp'
DOWNLOADER_EN = 'en'

DOWNLOADERS = [
    DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS, DOWNLOADER_RZ, DOWNLOADER_RP, DOWNLOADER_EN
]
RUXX_DOWNLOADERS = (DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS, DOWNLOADER_RZ, DOWNLOADER_RP, DOWNLOADER_EN)
RUN_FILE_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC)
PAGE_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC)
COLOR_LOG_DOWNLOADERS = (DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC)

APP_NAME_NM = DOWNLOADER_NM.upper()
APP_NAME_RV = DOWNLOADER_RV.upper()
APP_NAME_RC = DOWNLOADER_RC.upper()
APP_NAME_RUXX = 'Ruxx'
APP_NAMES = {
    DOWNLOADER_NM: APP_NAME_NM,
    DOWNLOADER_RV: APP_NAME_RV,
    DOWNLOADER_RC: APP_NAME_RC,
    DOWNLOADER_RN: APP_NAME_RUXX,
    DOWNLOADER_RX: APP_NAME_RUXX,
    DOWNLOADER_RS: APP_NAME_RUXX,
    DOWNLOADER_RZ: APP_NAME_RUXX,
    DOWNLOADER_RP: APP_NAME_RUXX,
    DOWNLOADER_EN: APP_NAME_RUXX,
}


class BaseConfig(object):
    DEFAULT_PATH = './'

    def __init__(self, *, test=False, console_log=False) -> None:
        # arguments
        # cmd
        self.debug = False
        self.no_download = False
        self.no_update = False
        self.install = False
        self.ignored_args: List[IgnoredArg] = list()
        self.override_ids: List[CatDwnIds] = list()
        self.downloaders: List[str] = list()
        self.categories: List[str] = list()
        self.script_path = ''
        # script
        self.dest_base = BaseConfig.DEFAULT_PATH
        self.dest_run_base = BaseConfig.DEFAULT_PATH
        self.dest_logs_base = BaseConfig.DEFAULT_PATH
        self.dest_bak_base = BaseConfig.DEFAULT_PATH
        self.title = ''
        self.title_increment = 0
        self.title_increment_value = ''
        self.python = ''
        self.datesub = True
        self.update = False
        self.update_offsets: Dict[str, int] = dict()
        # calculated
        self.max_cmd_len = MAX_CMD_LEN[OS_WINDOWS] // 2  # MAX_CMD_LEN.get(running_system())
        self.disabled_downloaders: Dict[str, Set[str]] = dict()
        # internal
        self.test = test
        self.console_log = not (test and not console_log)

    def _reset(self) -> None:
        self.__init__(test=self.test, console_log=self.console_log)

    @property
    def fulltitle(self) -> str:
        return f'{self.title}{self.title_increment_value}'

    def __str__(self) -> str:
        return (
            f'debug: {self.debug}, downloaders: {str(self.downloaders)}, script: {self.script_path}, dest: {self.dest_base}, '
            f'run: {self.dest_run_base}, logs: {self.dest_logs_base}, bak: {self.dest_bak_base}, update: {self.update}, '
            f'no_download: {self.no_download}, no_update: {self.no_update}, ignored_args: {str(self.ignored_args)}, '
            f'id_overrides: {str(self.override_ids)}, max_cmd_len: {self.max_cmd_len}'
        )

    __repr__ = __str__


Config = BaseConfig()

HELP_DEBUG = 'Run in debug mode (for development)'
HELP_DOWNLOADERS = f'Enabled downloaders. Default is all: \'{",".join(DOWNLOADERS)}\''
HELP_CATEGORIES = 'Enabled categories. Default is all'
HELP_NO_DOWNLOAD = 'Boolean flag to skip actual download (do not launch downloaders)'
HELP_NO_UPDATE = 'Boolean flag to skip script ids update regardless of script update flag being set or not'
HELP_INSTALL = 'Force install dependencies from enabled downloaders to selected Python\'s environment'
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

PATH_APPEND_DOWNLOAD_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_DOWNLOAD_NRVC_IDS = 'src/ids.py'
PATH_APPEND_DOWNLOAD_NRVC_PAGES = 'src/pages.py'
PATH_APPEND_UPDATE_RUXX = 'src/ruxx_cmd.py'
PATH_APPEND_UPDATE_NRVC = 'src/pages.py'
PATH_APPEND_REQUIREMENTS = 'requirements.txt'

PATH_APPEND_DOWNLOAD_IDS = {
    DOWNLOADER_NM: PATH_APPEND_DOWNLOAD_NRVC_IDS,
    DOWNLOADER_RV: PATH_APPEND_DOWNLOAD_NRVC_IDS,
    DOWNLOADER_RC: PATH_APPEND_DOWNLOAD_NRVC_IDS,
    DOWNLOADER_RN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RX: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RS: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RZ: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RP: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_EN: PATH_APPEND_DOWNLOAD_RUXX,
}
PATH_APPEND_DOWNLOAD_PAGES = {
    DOWNLOADER_NM: PATH_APPEND_DOWNLOAD_NRVC_PAGES,
    DOWNLOADER_RV: PATH_APPEND_DOWNLOAD_NRVC_PAGES,
    DOWNLOADER_RC: PATH_APPEND_DOWNLOAD_NRVC_PAGES,
    DOWNLOADER_RN: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RX: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RS: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RZ: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_RP: PATH_APPEND_DOWNLOAD_RUXX,
    DOWNLOADER_EN: PATH_APPEND_DOWNLOAD_RUXX,
}

PATH_APPEND_UPDATE = {
    DOWNLOADER_NM: PATH_APPEND_UPDATE_NRVC,
    DOWNLOADER_RV: PATH_APPEND_UPDATE_NRVC,
    DOWNLOADER_RC: PATH_APPEND_UPDATE_NRVC,
    DOWNLOADER_RN: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RX: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RS: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RZ: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_RP: PATH_APPEND_UPDATE_RUXX,
    DOWNLOADER_EN: PATH_APPEND_UPDATE_RUXX,
}

RANGE_ID_TEMPLATE_NRVC = StrPair(('-start %d', ' -end %d'))
RANGE_ID_TEMPLATE_RN_RP = StrPair(('id>=%d', ' id<=%d'))
RANGE_ID_TEMPLATE_RX_RS_RZ = StrPair(('id:>=%d', ' id:<=%d'))
RANGE_ID_TEMPLATE_EN = StrPair(('id:%d..', '%d'))
RANGE_PAGE_TEMPLATE_NRVC = StrPair(('-pages %d', ' -start %d'))
RANGE_PAGE_IDS_TEMPLATE_NRVC = StrPair(('-stop_id %d', '-begin_id %d'))

RANGE_TEMPLATE_IDS = {
    DOWNLOADER_NM: RANGE_ID_TEMPLATE_NRVC,
    DOWNLOADER_RV: RANGE_ID_TEMPLATE_NRVC,
    DOWNLOADER_RC: RANGE_ID_TEMPLATE_NRVC,
    DOWNLOADER_RN: RANGE_ID_TEMPLATE_RN_RP,
    DOWNLOADER_RX: RANGE_ID_TEMPLATE_RX_RS_RZ,
    DOWNLOADER_RS: RANGE_ID_TEMPLATE_RX_RS_RZ,
    DOWNLOADER_RZ: RANGE_ID_TEMPLATE_RX_RS_RZ,
    DOWNLOADER_RP: RANGE_ID_TEMPLATE_RN_RP,
    DOWNLOADER_EN: RANGE_ID_TEMPLATE_EN,
}

RANGE_TEMPLATE_PAGES = {
    DOWNLOADER_NM: RANGE_PAGE_TEMPLATE_NRVC,
    DOWNLOADER_RV: RANGE_PAGE_TEMPLATE_NRVC,
    DOWNLOADER_RC: RANGE_PAGE_TEMPLATE_NRVC,
}

RANGE_TEMPLATE_PAGE_IDS = {
    DOWNLOADER_NM: RANGE_PAGE_IDS_TEMPLATE_NRVC,
    DOWNLOADER_RV: RANGE_PAGE_IDS_TEMPLATE_NRVC,
    DOWNLOADER_RC: RANGE_PAGE_IDS_TEMPLATE_NRVC,
}

# must have __len__() defined
DT = TypeVar('DT', str, list, IntSequence)
WT = TypeVar('WT')
for _ in DT.__constraints__:
    assert hasattr(_, '__len__') and callable(getattr(_, '__len__')), f'DT class \'{_.__name__}\' doesn\'t have len() method!'


class DownloadCollection(Dict[str, Dict[str, Optional[DT]]]):
    """
    DownloadCollection is a dict which stores data of type **DT** per download module per download category
    """
    def __init__(self) -> None:
        super().__init__()

    def add_category(self, cat: str, init_type: Type[DT] = None, *args, **kwargs) -> None:
        self[cat] = {dt: self._make_init_value(init_type, *args, **kwargs) for dt in DOWNLOADERS}

    def cur(self) -> Dict[str, Optional[DT]]:
        return list(self.values())[-1]

    def cur_key(self) -> str:
        return list(self.keys())[-1]

    @staticmethod
    def _make_init_value(init_type: Type[DT], *args, **kwargs) -> DT:
        return init_type(*args, **kwargs) if init_type else None

    def _sub_to_str(self, cat: str) -> str:
        return f'\'{self[cat]}\': {",".join(f"{dt}[{len(self[cat][dt])}]" for dt in self[cat] if self[cat][dt]) or "None"}'

    def __str__(self) -> str:
        return '\n'.join(self._sub_to_str(cat) for cat in self)

    __repr__ = __str__


class Wrapper(Generic[WT]):
    def __init__(self, value: WT = None) -> None:
        self._value = value

    def get(self) -> Optional[WT]:
        return assert_notnull(self._value)

    def reset(self, value: WT = None) -> None:
        self.__init__(value)

    def __bool__(self) -> bool:
        return not not self._value

    def __str__(self) -> str:
        return str(self._value)

    __repr__ = __str__
    __call__ = get

#
#
#########################################
