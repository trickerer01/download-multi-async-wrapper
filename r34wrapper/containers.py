# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, NamedTuple, Type

from .defs import AT, DOWNLOADERS, DT, IntSequence, StrPair
from .util import assert_notnull

__all__ = ('CmdRunParams', 'DownloadCollection', 'Queries', 'Wrapper')


class DownloadCollection(Generic[DT]):
    """
    DownloadCollection is a dict which stores data of type **DT** per download module per download category
    """
    def __init__(self) -> None:
        self._container: dict[str, dict[str, DT | None]] = {}

    def __getitem__(self, item: str) -> dict[str, DT | None]:
        return self._container.__getitem__(item)

    def __setitem__(self, key: str, value: dict[str, DT | None]) -> None:
        self._container.__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        return self._container.__delitem__(key)

    def __len__(self) -> int:
        return len(self._container)

    def __iter__(self) -> Iterator[str]:
        return self._container.__iter__()

    def __eq__(self, other: DownloadCollection[DT]) -> bool:
        return self._container == other._container

    def items(self):
        return self._container.items()

    def update(self, mapping: DownloadCollection[DT] | dict[str, dict[str, DT | None]], **kwargs) -> None:
        return self._container.update(mapping._container if isinstance(mapping, DownloadCollection) else mapping, **kwargs)

    def add_category(self, cat: str, init_type: Type[DT] | None = None, *args, **kwargs) -> None:
        self[cat] = {dt: self._make_init_value(init_type, *args, **kwargs) for dt in DOWNLOADERS}

    @property
    def at_cur_cat(self) -> dict[str, DT | None]:
        return next(reversed(self._container.values()))

    @property
    def cur_cat(self) -> str:
        return next(reversed(self._container.keys()))

    @staticmethod
    def _make_init_value(init_type: Type[DT], *args, **kwargs) -> DT | None:
        return init_type(*args, **kwargs) if init_type else None

    def _sub_to_str(self, cat: str) -> str:
        return f'\'{self[cat]}\': {",".join(f"{dt}[{len(self[cat][dt]):d}]" for dt in self[cat] if self[cat][dt]) or "None"}'

    def __str__(self) -> str:
        return '\n'.join(self._sub_to_str(cat) for cat in self)

    __repr__ = __str__


class CmdRunParams(NamedTuple):
    query: str
    downloader: str
    downloader_query_num: int
    downloader_query_max: int
    category: str
    category_query_num: int
    category_query_max: int

    @property
    def dwn(self) -> str:
        return self.downloader

    @property
    def dqn(self) -> int:
        return self.downloader_query_num

    @property
    def dqm(self) -> int:
        return self.downloader_query_max

    @property
    def cat(self) -> str:
        return self.category

    @property
    def cqn(self) -> int:
        return self.category_query_num

    @property
    def cqm(self) -> int:
        return self.category_query_max


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
    __slots__ = frozenset[str]((
        'autoupdate_seqs',
        'proxies_update',
        'queries_file_lines',
        'sequences_common',
        'sequences_ids',
        'sequences_pages',
        'sequences_paths',
        'sequences_paths_reqs',
        'sequences_paths_update',
        'sequences_subfolders',
        'sequences_tags',
    ))

    compare_exclude_slots = frozenset[str](('queries_file_lines',))

    def __init__(self) -> None:
        self.queries_file_lines: list[str] | dict = []

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

    def __eq__(self, other) -> bool:
        return isinstance(other, Queries) and all(
            getattr(self, f) == getattr(other, f) for f in self.__slots__.difference(self.compare_exclude_slots)
        )

#
#
#########################################
