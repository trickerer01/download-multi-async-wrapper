# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import json
import os
import re

from config import Config
from containers import Queries
from defs import (
    BOOL_STRS,
    COLOR_LOG_DOWNLOADERS,
    DOWNLOADERS,
    MAX_CATEGORY_NAME_LENGTH,
    MIN_IDS_SEQ_LENGTH,
    PAGE_DOWNLOADERS,
    PARSER_TYPE_LIST,
    PARSER_TYPE_TXT,
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
from util import assert_notnull
from validators import positive_int, valid_dir_path

re_title = re.compile(r'^### TITLE:[A-zÀ-ʯА-я\d_+\-!]{,20}$')
re_title_incr = re.compile(r'^### TITLEINCREMENT:\d$')
re_dest_base = re.compile(r'^### DESTPATH:.+?$')
re_dest_bak = re.compile(r'^### BAKPATH:.+?$')
re_dest_run = re.compile(r'^### RUNPATH:.+?$')
re_dest_log = re.compile(r'^### LOGPATH:.+?$')
re_datesub = re.compile(r'^### DATESUB:.+?$')
re_update = re.compile(r'^### UPDATE:.+?$')
re_update_offsets = re.compile(r'^### UPDATE_OFFSETS:.+?$')
re_noproxy_fetches = re.compile(r'^### NOPROXY_FETCHES:.+?$')
re_category = re.compile(r'^### \(([A-zÀ-ʯА-я\d_+\-! ]+)\) ###$')
re_comment = re.compile(r'^##[^#].*?$')
re_python_exec = re.compile(r'^### PYTHON:.+?$')
re_downloader_type = re.compile(fr'^# (?:{"|".join(DOWNLOADERS)}|{"|".join(DOWNLOADERS).upper()})(?: .*?)?$')
re_ids_list = re.compile(r'^#(?:(?: \d+)+| -\d+)$')
re_pages_list = re.compile(r'^# p\d+(?: s\d+)?$')
re_downloader_basepath = re.compile(r'^# downloader:[A-Z/~].+?$')
re_common_arg = re.compile(r'^# common:-.+?$')
re_sub_begin = re.compile(r'^# sub:[^ ].*?$')
re_sub_end = re.compile(r'^# send$')
re_downloader_finalize = re.compile(r'^# end$')

__all__ = ('ParserText',)


class ParserText:
    def __init__(self) -> None:
        self.queries: Queries = Queries()

    @staticmethod
    def get_type_names() -> set[str]:
        return {PARSER_TYPE_LIST, PARSER_TYPE_TXT}

    def try_parse_proxy(self, pargs: list[str], ct: str, dl: str) -> None:
        proxy_idx = pargs.index(PROXY_ARG) if PROXY_ARG in pargs else -1
        if proxy_idx >= 0:
            assert len(pargs) > proxy_idx + 1, f'No {ct}:{dl} proxy argument found after \'-proxy\' argument'
            self.queries.proxies_update[dl] = StrPair(pargs[proxy_idx], pargs[proxy_idx + 1])

    def parse_queries_file(self) -> None:
        def cur_ct() -> str:
            try:
                return assert_notnull(cur_cat)
            except AssertionError:
                trace(f'\nat line {i + 1:d}: current download category isn\'t selected!')
                raise

        def cur_dl() -> str:
            try:
                return cur_ct() and assert_notnull(cur_dwn)
            except AssertionError:
                trace(f'\nat line {i + 1:d}: current downloader isn\'t selected!')
                raise

        args_to_ignore = Config.ignored_args.copy()
        cur_cat = cur_dwn = ''
        cur_tags_list: list[str] = []

        for i, line in enumerate(self.queries.queries_file_lines):
            try:
                line = line.strip(' \n\ufeff')  # remove BOM too
                if not line:
                    continue
                if line.startswith('###'):
                    if re_title.fullmatch(line):
                        title_base = line[line.find(':') + 1:]
                        trace(f'Parsed title: \'{title_base}\'')
                        assert not Config.title, 'Title can only be declared once!'
                        Config.title = title_base
                        continue
                    if re_title_incr.fullmatch(line):
                        title_incr_base = line[line.find(':') + 1:]
                        trace(f'Parsed title increment: \'{title_incr_base}\'')
                        assert Config.title_increment == 0, 'Title increment can only be declared once!'
                        Config.title_increment = positive_int(title_incr_base)
                        continue
                    if re_dest_base.fullmatch(line):
                        dest_base = line[line.find(':') + 1:]
                        trace(f'Parsed download dest base: \'{dest_base}\'')
                        assert Config.dest_base == Config.DEFAULT_PATH, f'Destination re-declaration! Was \'{Config.dest_base}\''
                        Config.dest_base = valid_dir_path(dest_base)
                        continue
                    if re_dest_bak.fullmatch(line):
                        dest_bak = line[line.find(':') + 1:]
                        trace(f'Parsed backup dest base: \'{dest_bak}\'')
                        assert Config.dest_bak_base == Config.DEFAULT_PATH, f'Backup path re-declaration! Was \'{Config.dest_bak_base}\''
                        Config.dest_bak_base = valid_dir_path(dest_bak)
                        continue
                    if re_dest_run.fullmatch(line):
                        dest_run = line[line.find(':') + 1:]
                        trace(f'Parsed run dest base: \'{dest_run}\'')
                        assert Config.dest_run_base == Config.DEFAULT_PATH, f'Run path re-declaration! Was \'{Config.dest_run_base}\''
                        Config.dest_run_base = valid_dir_path(dest_run)
                        continue
                    if re_dest_log.fullmatch(line):
                        dest_log = line[line.find(':') + 1:]
                        trace(f'Parsed logs dest base: \'{dest_log}\'')
                        assert Config.dest_logs_base == Config.DEFAULT_PATH, f'Logs path re-declaration! Was \'{Config.dest_logs_base}\''
                        Config.dest_logs_base = valid_dir_path(dest_log)
                        continue
                    if re_datesub.fullmatch(line):
                        datesub_str = line[line.find(':') + 1:]
                        trace(f'Parsed date subfolder flag value: \'{datesub_str}\' ({BOOL_STRS[datesub_str]!s})')
                        Config.datesub = BOOL_STRS[datesub_str]
                        continue
                    if re_update.fullmatch(line):
                        update_str = line[line.find(':') + 1:]
                        trace(f'Parsed update flag value: \'{update_str}\' ({BOOL_STRS[update_str]!s})')
                        if Config.no_update:
                            trace('UPDATE FLAG IS IGNORED DUE TO no_update FLAG')
                            assert Config.update is False
                        else:
                            Config.update = BOOL_STRS[update_str]
                        continue
                    if re_python_exec.fullmatch(line):
                        python_str = line[line.find(':') + 1:]
                        trace(f'Parsed python executable: \'{python_str}\'')
                        assert not Config.python, 'Python executable must be declared exactly once!'
                        Config.python = python_str
                        continue
                    if re_update_offsets.fullmatch(line):
                        offsets_str = line[line.find(':') + 1:]
                        trace(f'Parsed update offsets value: \'{offsets_str}\'')
                        assert Config.update_offsets == {}, f'Update offsets re-declaration! Was \'{Config.update_offsets!s}\''
                        Config.update_offsets = json.loads(offsets_str.lower())
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
                        assert not invalid_dts, f'Invalid update offsets value: {offsets_str}'
                        continue
                    if re_noproxy_fetches.fullmatch(line):
                        modules_str = line[line.find(':') + 1:]
                        trace(f'Parsed noproxy fetches value: \'{modules_str}\'')
                        assert Config.noproxy_fetches == set(), f'Noproxy fetches re-declaration! Was \'{Config.noproxy_fetches!s}\''
                        Config.noproxy_fetches = set(json.loads(modules_str.lower()))
                        invalid_dts: list[str] = []
                        for npdt in Config.noproxy_fetches:
                            if npdt not in DOWNLOADERS:
                                invalid_dts.append(npdt)
                                trace(f'Error: inavlid downloader type: \'{npdt}\'')
                        assert not invalid_dts, f'Invalid update offsets value: {modules_str}'
                        continue
                    ensure_logfile()
                    cat_match = re_category.fullmatch(line)
                    assert cat_match, f'at line {i + 1:d}: invalid category header format: \'{line}\'!'
                    cur_cat = cat_match.group(1)
                    if len(cur_ct()) > MAX_CATEGORY_NAME_LENGTH:
                        cur_cat = cur_ct()[:MAX_CATEGORY_NAME_LENGTH]
                        trace(f'Category name \'{cat_match.group(1)}\' is too long '
                              f'({len(cat_match.group(1))} > {len(cur_ct())})! Shrinked.')
                    if cur_ct() != cur_ct().strip():
                        trace(f'Category name \'{cur_ct()}\' will become \'{cur_ct().strip()}\' after stripping!')
                    assert cur_ct() not in self.queries.sequences_paths, f'Category \'{cur_ct()}\' already exists. Aborted!'
                    trace(f'Processing new category: \'{cur_ct()}\'...')
                    self.queries.sequences_ids.add_category(cur_ct())
                    self.queries.sequences_pages.add_category(cur_ct())
                    self.queries.sequences_paths.add_category(cur_ct())
                    self.queries.sequences_common.add_category(cur_ct(), list)
                    self.queries.sequences_tags.add_category(cur_ct(), list)
                    self.queries.sequences_subfolders.add_category(cur_ct(), list)
                    cur_tags_list.clear()
                    continue
                if line[0] not in '(-*#' and not line[0].isalnum():
                    trace(f'Error: corrupted line beginning found at line {i + 1:d}!')
                    raise OSError
                line = remove_trailing_comments(line)
                if line.startswith('#'):
                    if re_comment.fullmatch(line):
                        continue
                    ignored_idx: int
                    for ignored_idx in reversed(range(len(args_to_ignore))):
                        ignored_arg = args_to_ignore[ignored_idx]
                        start_idx = line.find(ignored_arg.name, line.find(':') + 1)
                        if start_idx > 0 and line[start_idx - 1] == '-':
                            start_idx -= 1
                            while start_idx and line[start_idx - 1] == '-':
                                start_idx -= 1
                            end_idx = start_idx + len(ignored_arg.name)
                            num_to_skip: int
                            for num_to_skip in reversed(range(ignored_arg.len)):
                                end_idx = line.find(' ', end_idx) + 1
                                if end_idx == 0:
                                    if num_to_skip == 0:
                                        end_idx = len(line)
                                    else:
                                        break
                                if num_to_skip == 0:
                                    # remove ignored arg(s) and consume ignored arg from config
                                    new_line = f'{line[:start_idx]}{line[min(end_idx, len(line)):]}'
                                    trace(f'Info: ignoring argument \'{ignored_arg!s}\' found at line {i + 1:d}:\n  \'{line}\' -->'
                                          f'\n  {" " * start_idx}^{" " * (end_idx - start_idx)}^\n  {new_line}')
                                    line = new_line
                                    del args_to_ignore[ignored_idx]
                    if not line or line.endswith(':'):
                        trace(f'Ignoring remnants of now consumed line {i + 1:d}: \'{line}\'')
                        continue
                    if re_downloader_type.fullmatch(line):
                        assert not cur_tags_list, f'at line {i + 1:d}: unclosed previous downloader section \'{cur_dl()}\'!'
                        cur_dwn = line.split(' ')[1].lower()
                        assert cur_dl() in DOWNLOADERS, f'at line {i + 1:d}: unknown downloader \'{cur_dl()}\'!'
                        trace(f'Processing \'{cur_dl().upper()}\' arguments...')
                        if cur_dl() in COLOR_LOG_DOWNLOADERS:
                            self.queries.sequences_common.at_cur_cat[cur_dl()].append('--disable-log-colors')
                    elif re_ids_list.fullmatch(line):
                        cdt = cur_dl()
                        cat = cur_ct()
                        idseq_i = IntSequence([int(num) for num in line.split(' ')[1:]], i + 1)
                        for ids_override in Config.override_ids:
                            if ids_override.name == f'{cat}:{cdt}':
                                idseq_temp = IntSequence(ids_override.ids, i + 1)
                                trace(f'Using \'{cat}:{cdt}\' ids override: {idseq_i!s} -> {idseq_temp!s}')
                                idseq_i.ints[:] = idseq_temp.ints[:]
                        if self.queries.sequences_pages.at_cur_cat[cdt]:
                            assert len(idseq_i) <= 2, (f'{cdt} has pages but defines ids range of '
                                                       f'{len(idseq_i):d} > 2!\n\tat line {i + 1}: {line}')
                        self.queries.sequences_ids.at_cur_cat[cdt] = idseq_i
                        if len(idseq_i) < MIN_IDS_SEQ_LENGTH:
                            if cdt in Config.downloaders:
                                negative_str = ' NEGATIVE' if idseq_i[0] < 0 else ''
                                trace(f'{cdt} at line {i + 1:d} provides a single{negative_str} id hence requires maxid autoupdate')
                                if cat not in self.queries.autoupdate_seqs:
                                    self.queries.autoupdate_seqs.add_category(cat)
                                self.queries.autoupdate_seqs[cat][cdt] = idseq_i
                            else:
                                idseq_i.ints.append(2**31 - 1)
                    elif re_pages_list.fullmatch(line):
                        cdt = cur_dl()
                        assert cdt in PAGE_DOWNLOADERS, f'{cur_cat}:{cdt} doesn\'t support pages search!\n\tat line {i + 1}: {line}'
                        idseq_p = self.queries.sequences_ids.at_cur_cat[cdt]
                        if idseq_p:
                            assert len(idseq_p) <= 2, (f'{cur_cat}:{cdt} defines pages but has ids range of '
                                                       f'{len(idseq_p):d} > 2!\n\tat line {i + 1}: {line}')
                        pageseq = IntSequence([int(num[1:]) for num in line.split(' ')[1:]], i + 1)
                        self.queries.sequences_pages.at_cur_cat[cdt] = pageseq
                        if len(pageseq) < MIN_IDS_SEQ_LENGTH:
                            pageseq.ints.append(1)
                    elif re_downloader_basepath.fullmatch(line):
                        cat = cur_ct()
                        cdt = cur_dl()
                        basepath = line[line.find(':') + 1:]
                        basepath_n = normalize_path(basepath)
                        path_append = (PATH_APPEND_DOWNLOAD_PAGES if self.queries.sequences_pages.at_cur_cat[cdt]
                                       else PATH_APPEND_DOWNLOAD_IDS)
                        path_downloader = f'{basepath_n}{path_append[cdt]}'
                        path_requirements = f'{basepath_n}{PATH_APPEND_REQUIREMENTS}'
                        path_updater = f'{basepath_n}{PATH_APPEND_UPDATE[cdt]}'
                        if Config.test is False:
                            assert os.path.isdir(basepath), f'{cat}:{cdt} base path \'{basepath}\' doesn\'t exist!'
                            assert os.path.isfile(path_downloader), f'{cat}:{cdt} downloader path \'{path_downloader}\' doesn\'t exist!'
                            if Config.install:
                                assert os.path.isfile(path_requirements), f'{cat}:{cdt} reqs file \'{path_requirements}\' doesn\'t exist!'
                            if Config.update:
                                assert os.path.isfile(path_updater), f'{cat}:{cdt} updater file \'{path_updater}\' doesn\'t exist!'
                        self.queries.sequences_paths.at_cur_cat[cur_dl()] = path_downloader
                        self.queries.sequences_paths_reqs[cur_dl()] = path_requirements
                        self.queries.sequences_paths_update[cur_dl()] = normalize_path(os.path.abspath(path_updater), False)
                    elif re_common_arg.fullmatch(line):
                        common_args = line[line.find(':') + 1:].split(' ')
                        self.try_parse_proxy(common_args, cur_ct(), cur_dl())
                        self.queries.sequences_common.at_cur_cat[cur_dl()].extend(common_args)
                    elif re_sub_begin.fullmatch(line):
                        cdt = cur_dl()
                        seq_subs, seq_tags = self.queries.sequences_subfolders, self.queries.sequences_tags
                        assert len(seq_subs.at_cur_cat[cdt]) == len(seq_tags.at_cur_cat[cdt]), f'Error: unclosed {cdt} sub!'
                        self.queries.sequences_subfolders.at_cur_cat[cur_dl()].append(line[line.find(':') + 1:])
                    elif re_sub_end.fullmatch(line):
                        self.queries.sequences_tags.at_cur_cat[cur_dl()].append(cur_tags_list.copy())
                    elif re_downloader_finalize.fullmatch(line):
                        cat, cdt = cur_ct(), cur_dl()
                        for extra_args in Config.extra_args:
                            if extra_args.is_for(cat, cdt):
                                trace(f'Using \'{cat}:{cdt}\' extra args: {extra_args.args!s} -> {" ".join(extra_args.args)}')
                                self.try_parse_proxy(extra_args.args, cur_ct(), cur_dl())
                                self.queries.sequences_common.at_cur_cat[cur_dl()].extend(f'"{arg}"' for arg in extra_args.args)
                        cur_tags_list.clear()
                        cur_dwn = ''
                    else:
                        trace(f'Error: unknown param at line {i + 1:d}!')
                        raise OSError
                else:  # elif line[0] in '(-*' or line[0].isalpha():
                    assert self.queries.sequences_ids.at_cur_cat[cur_dl()] or self.queries.sequences_pages.at_cur_cat[cur_dl()], (
                        f'Unbound tags found at line {i + 1:d}: {line}')
                    if '  ' in line:
                        trace(f'Error: double space found in tags at line {i + 1:d}!')
                        raise OSError
                    if line[0] != '(' and not line.startswith('-+(') and '~' in line:
                        trace(f'Error: unsupported ungrouped OR symbol at line {i + 1:d}!')
                        raise OSError
                    need_append = True
                    if all_tags_negative(line.split(' ')):  # line[0] === '-'
                        if line[1] in '-+':
                            # remove --tag(s) or -+tag(s) from list, convert: --a --b -> [-a, -b] OR -+a -+b -> [a, b]
                            tags_to_remove = [tag[2 if tag[1] == '+' else 1:] for tag in line.split(' ')]
                            for k in reversed(range(len(tags_to_remove))):
                                for j in reversed(range(len(cur_tags_list))):
                                    if cur_tags_list[j] == tags_to_remove[k]:
                                        del cur_tags_list[j]
                                        del tags_to_remove[k]
                                        break
                            assert len(tags_to_remove) == 0, f'Tags weren\'t consumed: "{" ".join(tags_to_remove)}" at line {i + 1}: {line}'
                            continue
                        else:
                            tags_split = [tag[1:] for tag in line.split(' ')]
                            split_len = len(tags_split)
                            assert all(bool(_) for _ in tags_split), f'Invalid tag string at line {i + 1:d}: {line}'
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
                                try_match_rem = split_len == 1 or cur_tag[::len(cur_tag) - 1] == '()'
                                if try_match_rem and cur_tag[start_idx:end_idx] == tags_rem:
                                    del cur_tags_list[j]
                                    need_find_previous_or_group = False
                                    break
                            if need_find_previous_or_group is True:
                                trace(f'Info: exclusion(s) at {i + 1:d}, no previous matching tag or \'or\' group found. Line: \'{line}\'')
                    elif not all_tags_positive(line.split(' ')):
                        param_like = line[0] == '-' and len(line.split(' ')) == 2
                        if not (param_like and (line.startswith(('-search', '-quality')))):
                            trace(f'Warning (W2): mixed positive / negative tags at line {i + 1:d}, '
                                  f'{"param" if param_like else "error"}? Line: \'{line}\'')
                    if need_append:
                        cur_tags_list.extend(line.split(' '))
            except Exception as e:
                trace(f'Error: issue encountered while parsing queries file at line {i + 1:d}!\n - {e!s}')
                raise

#
#
#########################################
