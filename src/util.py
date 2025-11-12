# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import itertools
from collections.abc import Iterable

from defs import AT


def unused_argument(arg: AT) -> None:
    _ = arg


def assert_notnull(obj: AT) -> AT:
    assert obj is not None
    return obj


def sum_lists(lists: Iterable[Iterable[AT]]) -> list[AT]:
    total: list[AT] = list(itertools.chain(*lists))
    return total

#
#
#########################################
