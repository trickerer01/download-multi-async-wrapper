# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import json
import os

from config import Config
from containers import Queries
from defs import (
    BOOL_STRS,
    COLOR_LOG_DOWNLOADERS,
    DOWNLOADERS,
    MAX_CATEGORY_NAME_LENGTH,
    MIN_IDS_SEQ_LENGTH,
    PAGE_DOWNLOADERS,
    PARSER_TYPE_JSON,
    PATH_APPEND_DOWNLOAD_IDS,
    PATH_APPEND_DOWNLOAD_PAGES,
    PATH_APPEND_REQUIREMENTS,
    PATH_APPEND_UPDATE,
    PROXY_ARG,
    IntSequence,
    StrPair,
)
from logger import ensure_logfile, trace
from strings import all_tags_negative, all_tags_positive, normalize_path, remove_trailing_comments
from validators import positive_int, valid_dir_path

__all__ = ('ParserJson',)


class ParserJson:
    def __init__(self) -> None:
        self.queries: Queries = Queries()
        self._json: dict = {}

    @staticmethod
    def get_type_names() -> set[str]:
        return {PARSER_TYPE_JSON}

    def try_parse_proxy(self, pargs: list[str], dl: str) -> None:
        proxy_idx = pargs.index(PROXY_ARG) if PROXY_ARG in pargs else -1
        if proxy_idx >= 0:
            assert len(pargs) > proxy_idx + 1
            self.queries.proxies_update[dl] = StrPair(pargs[proxy_idx], pargs[proxy_idx + 1])

    def parse_queries_file(self) -> None:
        args_to_ignore = Config.ignored_args.copy()
        cur_tags_list: list[str] = []

        json_clear = '\n'.join(filter(lambda l: l and not l.startswith('#'),
                                      (remove_trailing_comments(_.strip(' \n\ufeff')) for _ in self.queries.queries_file_lines)))
        try:
            self._json.update(json.loads(json_clear))
        except Exception:
            trace(f'Invalid json:\n"""\n{json_clear}\n"""')
            raise

        Config.title = self._json['title']
        trace(f'Parsed title: \'{Config.title}\'')
        Config.title_increment = positive_int(self._json['title_increment'])
        trace(f'Parsed title increment: \'{Config.title_increment}\'')
        Config.dest_base = valid_dir_path(self._json['dest_path'])
        trace(f'Parsed download dest base: \'{Config.dest_base}\'')
        Config.dest_bak_base = valid_dir_path(self._json['bak_path'])
        trace(f'Parsed backup dest base: \'{Config.dest_bak_base}\'')
        Config.dest_run_base = valid_dir_path(self._json['run_path'])
        trace(f'Parsed run dest base: \'{Config.dest_run_base}\'')
        Config.dest_logs_base = valid_dir_path(self._json['log_path'])
        trace(f'Parsed logs dest base: \'{Config.dest_logs_base}\'')
        Config.datesub = BOOL_STRS[self._json['date_sub']]
        trace(f'Parsed date subfolder flag value: \'{self._json["date_sub"]}\' ({BOOL_STRS[self._json["date_sub"]]!s})')
        Config.update = BOOL_STRS[self._json['update']]
        trace(f'Parsed update flag value: \'{self._json["update"]}\' ({BOOL_STRS[self._json["update"]]!s})')
        Config.update_offsets.update({k.lower(): v for k, v in self._json['update_offsets'].items()})
        trace(f'Parsed update offsets value: \'{Config.update_offsets!s}\'')
        Config.noproxy_fetches.update(self._json['noproxy_fetches'])
        trace(f'Parsed noproxy fetches value: \'{Config.noproxy_fetches!s}\'')
        Config.python = self._json['python']
        trace(f'Parsed python executable: \'{Config.python}\'')

        ensure_logfile()

        if Config.no_update and Config.update:
            trace('UPDATE FLAG IS IGNORED DUE TO no_update FLAG')
        if Config.update_offsets:
            invalid_dts: list[str] = []
            for pdt in Config.update_offsets:
                if pdt not in DOWNLOADERS:
                    invalid_dts.append(pdt)
                    trace(f'Error: inavlid downloader type: \'{pdt}\'')
                try:
                    int(Config.update_offsets[pdt])
                except ValueError:
                    invalid_dts.append(pdt)
                    trace(f'Error: invalid {pdt} offset int value: \'{Config.update_offsets[pdt]!s}\'')
            assert not invalid_dts, f'Invalid update offsets value: {self._json["update_offsets"]!s}'
        if Config.noproxy_fetches:
            invalid_dts: list[str] = []
            for npdt in Config.noproxy_fetches:
                if npdt not in DOWNLOADERS:
                    invalid_dts.append(npdt)
                    trace(f'Error: inavlid downloader type: \'{npdt}\'')
            assert not invalid_dts, f'Invalid update offsets value: {self._json["noproxy_fetches"]!s}'

        compose: dict[str, dict[str, dict[str, None | str | list[str] | list[dict[str, list[str]]]]]] = self._json['compose']

        for cat, dts in compose.items():
            if len(cat) > MAX_CATEGORY_NAME_LENGTH:
                cat_orig, cat = cat, cat[:MAX_CATEGORY_NAME_LENGTH]
                trace(f'Category name \'{cat_orig}\' is too long ({len(cat_orig)} > {len(cat)})! Shrinked.')
            if cat != cat.strip():
                trace(f'Category name \'{cat}\' will become \'{cat.strip()}\' after stripping!')
            trace(f'Processing new category: \'{cat}\'...')
            self.queries.sequences_ids.add_category(cat)
            self.queries.sequences_pages.add_category(cat)
            self.queries.sequences_paths.add_category(cat)
            self.queries.sequences_common.add_category(cat, list)
            self.queries.sequences_tags.add_category(cat, list)
            self.queries.sequences_subfolders.add_category(cat, list)
            cur_tags_list.clear()
            for cdt, entries in dts.items():
                cdt = cdt.lower()
                assert cdt in DOWNLOADERS, f'at cat \'{cat}\': unknown downloader \'{cdt}\'!'
                trace(f'Processing \'{cdt.upper()}\' arguments...')
                if cdt in COLOR_LOG_DOWNLOADERS:
                    self.queries.sequences_common.at_cur_cat[cdt].append('--disable-log-colors')
                pages: list[str] | None = entries['pages']
                if pages:
                    assert cdt in PAGE_DOWNLOADERS, f'{cat}:{cdt} doesn\'t support pages search!'
                    idseq = self.queries.sequences_ids.at_cur_cat[cdt]
                    if idseq:
                        assert len(idseq) <= 2, f'{cat}:{cdt} defines pages but has ids range of {len(idseq):d} > 2!\n\t{idseq!s}'
                    pageseq = IntSequence([int(num[1:]) for num in pages], 0)
                    self.queries.sequences_pages.at_cur_cat[cdt] = pageseq
                    if len(pageseq) < MIN_IDS_SEQ_LENGTH:
                        pageseq.ints.append(1)
                ids: list[str] = entries['ids']
                idseq = IntSequence([int(num) for num in ids], 0)
                for ids_override in Config.override_ids:
                    if ids_override.name == f'{cat}:{cdt}':
                        idseq_temp = IntSequence(ids_override.ids, 0)
                        trace(f'Using \'{cat}:{cdt}\' ids override: {idseq!s} -> {idseq_temp!s}')
                        idseq = idseq_temp
                if self.queries.sequences_pages.at_cur_cat[cdt]:
                    assert len(idseq) <= 2, f'{cat}:{cdt} has pages but defines ids range of {len(idseq):d} > 2!\n\t{ids!s}'
                self.queries.sequences_ids.at_cur_cat[cdt] = idseq
                if len(idseq) < MIN_IDS_SEQ_LENGTH:
                    if cdt in Config.downloaders:
                        negative_str = ' NEGATIVE' if idseq[0] < 0 else ''
                        trace(f'{cat}:{cdt} provides a single{negative_str} id hence requires maxid autoupdate')
                        if cat not in self.queries.autoupdate_seqs:
                            self.queries.autoupdate_seqs.add_category(cat)
                        self.queries.autoupdate_seqs[cat][cdt] = idseq
                    else:
                        idseq.ints.append(2**31 - 1)
                basepath: str = entries['downloader']
                basepath_n = normalize_path(basepath)
                path_append = PATH_APPEND_DOWNLOAD_PAGES if self.queries.sequences_pages.at_cur_cat[cdt] else PATH_APPEND_DOWNLOAD_IDS
                path_downloader = f'{basepath_n}{path_append[cdt]}'
                path_requirements = f'{basepath_n}{PATH_APPEND_REQUIREMENTS}'
                path_updater = f'{basepath_n}{PATH_APPEND_UPDATE[cdt]}'
                if Config.test is False:
                    assert os.path.isdir(basepath)
                    assert os.path.isfile(path_downloader)
                    if Config.install:
                        assert os.path.isfile(path_requirements)
                    if Config.update:
                        assert os.path.isfile(path_updater)
                self.queries.sequences_paths.at_cur_cat[cdt] = path_downloader
                self.queries.sequences_paths_reqs[cdt] = path_requirements
                self.queries.sequences_paths_update[cdt] = normalize_path(os.path.abspath(path_updater), False)
                common_args_list: list[str] = entries['common']
                for i, common in enumerate(common_args_list):
                    common_orig = common
                    ignored_idx: int
                    for ignored_idx in reversed(range(len(args_to_ignore))):
                        ignored_arg = args_to_ignore[ignored_idx]
                        start_idx = common.find(ignored_arg.name, common.find(':') + 1)
                        if start_idx > 0 and common[start_idx - 1] == '-':
                            start_idx -= 1
                            while start_idx and common[start_idx - 1] == '-':
                                start_idx -= 1
                            end_idx = start_idx + len(ignored_arg.name)
                            num_to_skip: int
                            for num_to_skip in reversed(range(ignored_arg.len)):
                                end_idx = common.find(' ', end_idx) + 1
                                if end_idx == 0:
                                    if num_to_skip == 0:
                                        end_idx = len(common)
                                    else:
                                        break
                                if num_to_skip == 0:
                                    # remove ignored arg(s) and consume ignored arg from config
                                    new_common = f'{common[:start_idx]}{common[min(end_idx, len(common)):]}'
                                    trace(f'Info: ignoring argument \'{ignored_arg!s}\' found at common {i + 1:d}:\n  \'{common}\' -->'
                                          f'\n  {" " * start_idx}^{" " * (end_idx - start_idx)}^\n  {new_common}')
                                    common = new_common
                                    del args_to_ignore[ignored_idx]
                    if not common:
                        trace(f'Common argument \'{common_orig}\' was fully consumed by ignored args (was offset {i:d})')
                        continue
                    common_args = common.split(' ')
                    self.try_parse_proxy(common_args, cdt)
                    self.queries.sequences_common.at_cur_cat[cdt].extend(common_args)
                subs: list[dict[str, list[str]]] = entries['subs']
                for sub_index, sub in enumerate(subs):
                    assert len(sub) == 1, f'Malformed {cat}:{cdt} sub at offest {sub_index:d}!'
                    # this ineffecient way of assignment helps the linter and saves 2 lines of annotations
                    sub_name, stages = next(iter(sub.keys())), next(iter(sub.values()))
                    if stages:
                        self.queries.sequences_subfolders.at_cur_cat[cdt].append(sub_name)
                        for i, stage in enumerate(stages):
                            assert stage, f'{cat}:{cdt} has empty arguments string found in sub \'{sub_name}\' at offset {i:d}!'
                            if stage[0] not in '(-*' and not stage[0].isalnum():
                                trace(f'Error: corrupted {cat}:{cdt} sub line beginning in sub \'{sub_name}\' at offset {i:d}!')
                                raise OSError
                            if '  ' in stage:
                                trace(f'Error: double space found in {cat}:{cdt} sub \'{sub_name}\' tags at offset {i:d}!')
                                raise OSError
                            if stage[0] != '(' and not stage.startswith('-+(') and '~' in stage:
                                trace(f'Error: unsupported ungrouped OR symbol in {cat}:{cdt} sub \'{sub_name}\' at offset {i:d}!')
                                raise OSError
                            need_append = True
                            if all_tags_negative(stage.split(' ')):  # line[0] === '-'
                                if stage[1] in '-+':
                                    # remove --tag(s) or -+tag(s) from list, convert: --a --b -> [-a, -b] OR -+a -+b -> [a, b]
                                    tags_to_remove = [tag[2 if tag[1] == '+' else 1:] for tag in stage.split(' ')]
                                    for k in reversed(range(len(tags_to_remove))):
                                        for j in reversed(range(len(cur_tags_list))):
                                            if cur_tags_list[j] == tags_to_remove[k]:
                                                del cur_tags_list[j]
                                                del tags_to_remove[k]
                                                break
                                    assert len(tags_to_remove) == 0, (f'Tags weren\'t consumed: "{" ".join(tags_to_remove)}" '
                                                                      f'in {cat}:{cdt} sub \'{sub_name}\' at offset {i:d}')
                                    continue
                                else:
                                    tags_split = [tag[1:] for tag in stage.split(' ')]
                                    split_len = len(tags_split)
                                    assert all(len(tag) > 0 for tag in tags_split)
                                    need_find_previous_or_group = True
                                    tags_rem = '~'.join(tags_split)
                                    tags_search = ','.join(tags_split)
                                    start_idx = 1 if split_len > 1 else 0
                                    end_idx = -1 if split_len > 1 else None
                                    j: int
                                    for j in reversed(range(len(cur_tags_list))):
                                        cur_tag = cur_tags_list[j]
                                        prev_tag = cur_tags_list[j - 1] if j > 0 else ''
                                        try_match_search = j > 0 and prev_tag.startswith('-search')
                                        if try_match_search and cur_tag == tags_search:
                                            del cur_tags_list[j]
                                            del cur_tags_list[j - 1]
                                            need_find_previous_or_group = False
                                            if prev_tag == '-search' or prev_tag.startswith('-search_rule'):
                                                need_append = False
                                            break
                                        try_match_rem = split_len == 1 or cur_tag[::max(len(cur_tag) - 1, 1)] == '()'
                                        if try_match_rem and cur_tag[start_idx:end_idx] == tags_rem:
                                            del cur_tags_list[j]
                                            need_find_previous_or_group = False
                                            break
                                    if need_find_previous_or_group is True:
                                        trace(f'Info: exclusion(s): no previous matching tag or \'or\' group found '
                                              f'in {cat}:{cdt} sub \'{sub_name}\' at offset {i:d}')
                            elif not all_tags_positive(stage.split(' ')):
                                param_like = stage[0] == '-' and len(stage.split(' ')) == 2
                                if not (param_like and (stage.startswith(('-search', '-quality')))):
                                    trace(f'Warning (W2): mixed positive / negative tags in {cat}:{cdt} sub\'{sub_name}\' at offset {i:d}, '
                                          f'{"param" if param_like else "error"}? Line: \'{stage}\'')
                            if need_append:
                                cur_tags_list.extend(stage.split(' '))
                        self.queries.sequences_tags.at_cur_cat[cdt].append(cur_tags_list.copy())
                for extra_args in Config.extra_args:
                    if extra_args.name == f'{cat}:{cdt}':
                        trace(f'Using \'{cat}:{cdt}\' extra args: {extra_args.args!s} -> {" ".join(extra_args.args)}')
                        self.try_parse_proxy(extra_args.args, cdt)
                        self.queries.sequences_common.at_cur_cat[cdt].extend(f'"{arg}"' for arg in extra_args.args)
                cur_tags_list.clear()

#
#
#########################################
