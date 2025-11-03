# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Dict, Generic, Type

from defs import AT, DOWNLOADERS, DT, IntSequence, StrPair
from util import assert_notnull


class DownloadCollection(Dict[str, Dict[str, DT | None]]):
    """
    DownloadCollection is a dict which stores data of type **DT** per download module per download category
    """
    def __init__(self) -> None:
        super().__init__()

    def add_category(self, cat: str, init_type: Type[DT] | None = None, *args, **kwargs) -> None:
        self[cat] = {dt: self._make_init_value(init_type, *args, **kwargs) for dt in DOWNLOADERS}

    @property
    def at_cur_cat(self) -> dict[str, DT | None]:
        return next(reversed(self.values()))

    @property
    def cur_cat(self) -> str:
        return next(reversed(self.keys()))

    @staticmethod
    def _make_init_value(init_type: Type[DT], *args, **kwargs) -> DT | None:
        return init_type(*args, **kwargs) if init_type else None

    def _sub_to_str(self, cat: str) -> str:
        return f'\'{self[cat]}\': {",".join(f"{dt}[{len(self[cat][dt])}]" for dt in self[cat] if self[cat][dt]) or "None"}'

    def __str__(self) -> str:
        return '\n'.join(self._sub_to_str(cat) for cat in self)

    __repr__ = __str__


class Wrapper(Generic[AT]):
    _value: AT | None

    def __init__(self, value: AT | None = None) -> None:
        self.reset(value)

    @property
    def val(self) -> AT:
        return assert_notnull(self._value)

    def reset(self, value: AT | None = None) -> None:
        self._value = value

    def __bool__(self) -> bool:
        return bool(self._value)

    def __str__(self) -> str:
        return str(self._value)

    __repr__ = __str__


class Queries:
    def __init__(self) -> None:
        self.queries_file_lines: list[str] = []

        self.autoupdate_seqs: DownloadCollection[IntSequence] = DownloadCollection()

        self.sequences_ids: DownloadCollection[IntSequence] = DownloadCollection()
        self.sequences_pages: DownloadCollection[IntSequence] = DownloadCollection()
        self.sequences_paths: DownloadCollection[str] = DownloadCollection()
        self.sequences_common: DownloadCollection[list[str]] = DownloadCollection()
        self.sequences_tags: DownloadCollection[list[list[str]]] = DownloadCollection()
        self.sequences_subfolders: DownloadCollection[list[str]] = DownloadCollection()

        self.sequences_paths_reqs: dict[str, str | None] = dict.fromkeys(DOWNLOADERS)
        self.sequences_paths_update: dict[str, str | None] = dict.fromkeys(DOWNLOADERS)
        self.proxies_update: dict[str, StrPair | None] = dict.fromkeys(DOWNLOADERS)
        self.maxid_fetched: dict[str, int] = {}

#
#
#########################################
