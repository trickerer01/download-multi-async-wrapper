# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from typing import Protocol

from ._parsers import ParserJson, ParserText
from .config import Config
from .containers import Queries
from .defs import (
    PARSER_TYPE_AUTO,
    PARSER_TYPE_JSON,
    PARSER_TYPE_LIST,
    PARSER_TYPE_TXT,
)
from .logger import trace

__all__ = ('ParserMeta', 'create_parser', 'register_parser_type')


class ParserMeta(Protocol):
    queries: Queries

    @staticmethod
    def get_type_names() -> set[str]: ...

    def parse_queries_file(self) -> None: ...


PARSERS: dict[str, ParserMeta] = {
    PARSER_TYPE_JSON: ParserJson(),
    PARSER_TYPE_LIST: ParserText(),
    PARSER_TYPE_TXT: ParserText(),
}


# internally unused
def register_parser_type(parser_type_str: str, parser_type: ParserMeta):
    assert parser_type_str not in PARSERS, (f'parser {parser_type_str} is already registered: '
                                            f'\'{PARSERS[parser_type_str].__class__.__name__}\'!')
    PARSERS.update({parser_type_str: parser_type})


def select_parser_type() -> str:
    if Config.parser_type == PARSER_TYPE_AUTO:
        trace(f'Parser type is \'{PARSER_TYPE_AUTO}\', autopicking...')
        ext = os.path.splitext(Config.script_path)[1]
        parser_type = ext[ext.rfind('.') + 1:]
        trace(f'...utopicked parser type \'{parser_type}\'')
    else:
        parser_type = Config.parser_type
    return parser_type


def create_parser() -> ParserMeta:
    parser_type = select_parser_type()
    parser = PARSERS.get(parser_type)
    assert parser, f'No parser registered for parser type {parser_type}!'
    return parser.__class__()

#
#
#########################################
