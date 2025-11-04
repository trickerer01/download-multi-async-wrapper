# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Protocol

from config import Config
from containers import Queries
from defs import (
    PARSER_TYPE_LIST,
    PARSER_TYPE_TXT,
)
from parser_text import ParserText

__all__ = ('ParserMeta', 'create_parser', 'register_parser_type')


class ParserMeta(Protocol):
    queries: Queries

    @staticmethod
    def get_type_names() -> set[str]: ...

    def parse_queries_file(self) -> None: ...


PARSERS: dict[str, ParserMeta] = {
    PARSER_TYPE_LIST: ParserText(),
    PARSER_TYPE_TXT: ParserText(),
}


# intrnally unused
def register_parser_type(parser_type_str: str, parser_type: ParserMeta):
    assert parser_type_str not in PARSERS, (f'parser {parser_type_str} is already registered: '
                                            f'\'{PARSERS[parser_type_str].__class__.__name__}\'!')
    PARSERS.update({parser_type_str: parser_type})


def create_parser() -> ParserMeta:
    parser = PARSERS.get(Config.parser_type)
    assert parser, f'No parser registered for parser type {Config.parser_type}!'
    return parser.__class__()


#
#
#########################################
