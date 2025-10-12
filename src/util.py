# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from defs import AT


def unused_argument(arg: AT) -> None:
    _ = arg


def assert_notnull(obj: AT) -> AT:
    assert obj is not None
    return obj

#
#
#########################################
