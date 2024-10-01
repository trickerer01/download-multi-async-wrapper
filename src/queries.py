# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
import sys
from collections.abc import Iterable
from json import loads
from os import chmod, path, stat, listdir
from re import compile as re_compile
from subprocess import CalledProcessError, check_output
from threading import Thread, Lock as ThreadLock

from cmdargs import valid_dir_path, positive_int
from defs import (
    DownloadCollection, Wrapper, IntSequence, Config, StrPair, UTF8, DOWNLOADERS, MIN_IDS_SEQ_LENGTH, PATH_APPEND_DOWNLOAD_IDS,
    PATH_APPEND_DOWNLOAD_PAGES, PATH_APPEND_UPDATE, PATH_APPEND_REQUIREMENTS, RUXX_DOWNLOADERS, PAGE_DOWNLOADERS, PROXY_ARG,
    MAX_CATEGORY_NAME_LENGTH, BOOL_STRS, COLOR_LOG_DOWNLOADERS,
)
from executor import register_queries
from logger import trace, ensure_logfile
from sequences import validate_sequences, form_queries, report_queries, validate_runners, report_unoptimized
from strings import SLASH, NEWLINE, datetime_str_nfull, all_tags_negative, all_tags_positive, normalize_path

__all__ = ('read_queries_file', 'prepare_queries', 'update_next_ids', 'at_startup')

re_title = re_compile(r'^### TITLE:[A-zÀ-ʯА-я\d_+\-!]{,20}$')
re_title_incr = re_compile(r'^### TITLEINCREMENT:\d$')
re_dest_base = re_compile(r'^### DESTPATH:.+?$')
re_dest_bak = re_compile(r'^### BAKPATH:.+?$')
re_dest_run = re_compile(r'^### RUNPATH:.+?$')
re_dest_log = re_compile(r'^### LOGPATH:.+?$')
re_datesub = re_compile(r'^### DATESUB:.+?$')
re_update = re_compile(r'^### UPDATE:.+?$')
re_update_offsets = re_compile(r'^### UPDATE_OFFSETS:.+?$')
re_category = re_compile(r'^### \(([A-zÀ-ʯА-я\d_+\-! ]+)\) ###$')
re_comment = re_compile(r'^##[^#].*?$')
re_python_exec = re_compile(r'^### PYTHON:.+?$')
re_downloader_type = re_compile(fr'^# (?:{"|".join(DOWNLOADERS)}|{"|".join(DOWNLOADERS).upper()})(?: .*?)?$')
re_ids_list = re_compile(r'^#(?:(?: \d+)+| -\d+)$')
re_pages_list = re_compile(r'^# p\d+(?: s\d+)?$')
re_downloader_basepath = re_compile(r'^# downloader:[A-Z/~].+?$')
re_common_arg = re_compile(r'^# common:-.+?$')
re_sub_begin = re_compile(r'^# sub:[^ ].*?$')
re_sub_end = re_compile(r'^# send$')
re_downloader_finalize = re_compile(r'^# end$')

queries_file_lines: Wrapper[list[str]] = Wrapper()

sequences_ids: DownloadCollection[IntSequence] = DownloadCollection()
sequences_pages: DownloadCollection[IntSequence] = DownloadCollection()
sequences_paths: DownloadCollection[str] = DownloadCollection()
sequences_common: DownloadCollection[list[str]] = DownloadCollection()
sequences_tags: DownloadCollection[list[list[str]]] = DownloadCollection()
sequences_subfolders: DownloadCollection[list[str]] = DownloadCollection()

sequences_paths_reqs: dict[str, str | None] = {dt: None for dt in DOWNLOADERS}
sequences_paths_update: dict[str, str | None] = {dt: None for dt in DOWNLOADERS}
proxies_update: dict[str, StrPair | None] = {dt: None for dt in DOWNLOADERS}
maxid_fetched: dict[str, int] = dict()


def ensure_logfile_wrapper() -> None:
    if Config.title_increment > 0 and not Config.title_increment_value:
        if not Config.title:
            trace('Warning: title suffix increment is defined but no title set!')
        else:
            if Config.dest_logs_base == Config.DEFAULT_PATH:
                trace('Warning: logs path is unset, title suffix increment will use base path to look for log files')
            calculate_title_suffix()
    ensure_logfile()


def calculate_title_suffix() -> None:
    trace('Calculating title suffix...')
    lbdir = Config.dest_logs_base
    logsdir_all: list[str] = listdir(lbdir) if path.isdir(lbdir) else []
    logsdir_files = list(filter(
        lambda x: x.startswith((f'log_{Config.title}', f'run_{Config.title}')) and path.isfile(f'{lbdir}{x}'), logsdir_all
    ))
    max_suffix_len = Config.title_increment
    max_suffix_val = 0
    base_idx = len(f'log_{Config.title}')
    for fname in logsdir_files:
        sep_idx = fname.find('_', base_idx)
        if sep_idx > base_idx:
            suffix_val = fname[base_idx:sep_idx]
            if suffix_val.isnumeric():
                max_suffix_len = max(max_suffix_len, len(suffix_val))
                max_suffix_val = max(max_suffix_val, int(suffix_val))
    Config.title_increment_value = f'{max_suffix_val + 1:0{max_suffix_len:d}d}'
    trace(f'Suffix calculated: \'{Config.title_increment_value}\'. Full title: \'{Config.full_title}\'')


def fetch_maxids(dts: Iterable[str]) -> dict[str, str]:
    try:
        if not dts:
            return {}
        trace('Fetching max ids...')
        re_maxid_fetch_result = re_compile(r'^[A-Z]{2}: \d+$')
        grab_threads = list()
        results: dict[str, str] = {dt: '' for dt in dts if sequences_paths_update[dt] is not None}
        rlock = ThreadLock()

        def get_max_id(dtype: str) -> None:
            update_file_path = sequences_paths_update[dtype]
            module_arguments: list[str] = ['-module', dtype] if dtype in RUXX_DOWNLOADERS else list()
            if dtype in proxies_update and proxies_update[dtype]:
                module_arguments += [proxies_update[dtype].first, proxies_update[dtype].second]
            arguments = [Config.python, update_file_path, '-get_maxid', '-timeout', '30'] + module_arguments
            try:
                res = check_output(arguments.copy()).decode(errors='replace').strip()
            except (KeyboardInterrupt, CalledProcessError):
                res = 'ERROR'
            with rlock:
                results[dtype] = res[res.rfind('\n') + 1:]

        for dt in results:
            grab_threads.append(Thread(target=get_max_id, args=(dt,)))
            grab_threads[-1].start()
        while grab_threads:
            thread = grab_threads.pop(-1)
            while thread.is_alive():
                try:
                    thread.join()
                except KeyboardInterrupt:
                    # Race condition may prevent thread from joining: https://bugs.python.org/issue45274
                    if sys.version_info < (3, 11):
                        for threadx in [thread, *grab_threads]:
                            if threadx._tstate_lock.locked(): threadx._tstate_lock.release()  # noqa
                            threadx._stop()  # noqa
        res_errors = list()
        for dt in results:
            try:
                assert re_maxid_fetch_result.fullmatch(results[dt])
            except AssertionError:
                res_errors.append(f'Error in fetch \'{dt}\' max id result!')
                continue
        assert len(res_errors) == 0, '\n ' + '\n '.join(res_errors)

        trace(NEWLINE.join(results[dt] for dt in results))
        return results
    except AssertionError:
        trace('\nError: failed to fetch next ids!\n')
        raise


def read_queries_file() -> None:
    trace(f'\nReading queries file: \'{Config.script_path}\'')
    with open(Config.script_path, 'rt', encoding=UTF8) as qfile:
        queries_file_lines.reset(qfile.readlines())


def prepare_queries() -> None:
    def cur_dl() -> str:
        try:
            assert sequences_paths
        except AssertionError:
            trace(f'\nat line {i + 1:d}: current download category isn\'t selected!')
            raise
        try:
            assert cur_dwn
            return cur_dwn
        except AssertionError:
            trace(f'\nat line {i + 1:d}: current downloader isn\'t selected!')
            raise

    def cur_category() -> str:
        try:
            assert sequences_paths
            return sequences_paths.cur_key()
        except AssertionError:
            trace(f'\nat line {i + 1:d}: current download category isn\'t selected!')
            raise

    cur_dwn = ''
    cur_tags_list = list()
    autoupdate_seqs: DownloadCollection[IntSequence] = DownloadCollection()

    trace('Analyzing queries file strings...')

    i: int
    line: str
    for i, line in enumerate(queries_file_lines()):
        try:
            line = line.strip(' \n\ufeff')  # remove BOM too
            if line == '':
                continue
            if line.startswith('###'):
                if re_title.fullmatch(line):
                    title_base = line[line.find(':') + 1:]
                    trace(f'Parsed title: \'{title_base}\'')
                    assert Config.title == '', 'Title can only be declared once!'
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
                    trace(f'Parsed date subfolder flag value: \'{datesub_str}\' ({str(BOOL_STRS.get(datesub_str))})')
                    Config.datesub = BOOL_STRS[datesub_str]
                    continue
                if re_update.fullmatch(line):
                    update_str = line[line.find(':') + 1:]
                    trace(f'Parsed update flag value: \'{update_str}\' ({str(BOOL_STRS.get(update_str))})')
                    if Config.no_update:
                        trace('UPDATE FLAG IS IGNORED DUE TO no_update FLAG')
                        assert Config.update is False
                    else:
                        Config.update = BOOL_STRS[update_str]
                    continue
                if re_python_exec.fullmatch(line):
                    python_str = line[line.find(':') + 1:]
                    trace(f'Parsed python executable: \'{python_str}\'')
                    assert Config.python == '', 'Python executable must be declared exactly once!'
                    Config.python = python_str
                    continue
                if re_update_offsets.fullmatch(line):
                    offsets_str = line[line.find(':') + 1:]
                    trace(f'Parsed update offsets value: \'{offsets_str}\'')
                    assert Config.update_offsets == {}, f'Update offsets re-declaration! Was \'{str(Config.update_offsets)}\''
                    Config.update_offsets = loads(offsets_str.lower())
                    invalid_dts = list()
                    for pdt in Config.update_offsets:
                        if pdt not in DOWNLOADERS:
                            invalid_dts.append(pdt)
                            trace(f'Error: inavlid downloader type: \'{pdt}\'')
                        try:
                            int(Config.update_offsets[pdt])
                        except ValueError:
                            invalid_dts.append(pdt)
                            trace(f'Error: invalid {pdt} offset int value: \'{Config.update_offsets[pdt]}\'')
                    assert not invalid_dts, f'Invalid update offsets value: {offsets_str}'
                    continue
                ensure_logfile_wrapper()
                cat_match = re_category.fullmatch(line)
                assert cat_match, f'at line {i + 1:d}: invalid category header format: \'{line}\'!'
                cur_cat = cat_match.group(1)
                if len(cur_cat) > MAX_CATEGORY_NAME_LENGTH:
                    cur_cat = cur_cat[:MAX_CATEGORY_NAME_LENGTH]
                    trace(f'Category name \'{cat_match.group(1)}\' is too long ({len(cat_match.group(1))} > {len(cur_cat)})! Shrinked.')
                if cur_cat != cur_cat.strip():
                    trace(f'Category name \'{cur_cat}\' will become \'{cur_cat.strip()}\' after stripping!')
                assert cur_cat not in sequences_paths, f'Category \'{cur_cat}\' already exists. Aborted!'
                trace(f'Processing new category: \'{cur_cat}\'...')
                sequences_ids.add_category(cur_cat)
                sequences_pages.add_category(cur_cat)
                sequences_paths.add_category(cur_cat)
                sequences_common.add_category(cur_cat, list)
                sequences_tags.add_category(cur_cat, list)
                sequences_subfolders.add_category(cur_cat, list)
                cur_tags_list.clear()
                continue
            if line[0] not in '(-*#' and not line[0].isalnum():
                trace(f'Error: corrupted line beginning found at line {i + 1:d}!')
                raise IOError
            if line.startswith('#'):
                if re_comment.fullmatch(line):
                    # trace(f'Ignoring commented out line {i + 1:d}: \'{line}\'')
                    continue
                skipped_idx = -1
                for ignored_idx, ignored in enumerate(Config.ignored_args):
                    start_idx = line.find(': ') + 2 if ': ' in line else 0
                    start_idx = line.find(ignored.name, start_idx)
                    if start_idx > 0 and line[start_idx - 1] == '-':
                        if ignored.len < 2 or line.find(' ', start_idx + len(ignored.name)) > start_idx:
                            skipped_idx = ignored_idx
                            break
                if skipped_idx >= 0:
                    trace(f'Info: ignoring argument \'{str(Config.ignored_args[skipped_idx])}\' found at line {i + 1:d}. line: \'{line}\'')
                    continue
                if re_downloader_type.fullmatch(line):
                    assert not cur_tags_list, f'at line {i + 1:d}: unclosed previous downloader section \'{cur_dwn}\'!'
                    cur_dwn = line.split(' ')[1].lower()
                    assert cur_dwn in DOWNLOADERS, f'at line {i + 1:d}: unknown downloader \'{cur_dwn}\'!'
                    trace(f'Processing \'{cur_dl().upper()}\' arguments...')
                    if cur_dl() in COLOR_LOG_DOWNLOADERS:
                        sequences_common.cur()[cur_dl()].append('--disable-log-colors')
                elif re_ids_list.fullmatch(line):
                    cdt = cur_dl()
                    cat = cur_category()
                    idseq = IntSequence([int(num) for num in line.split(' ')[1:]], i + 1)
                    for ids_override in Config.override_ids:
                        if ids_override.name == f'{cat}:{cdt}':
                            idseq_temp = IntSequence(ids_override.ids, i + 1)
                            trace(f'Using \'{cat}:{cdt}\' ids override: {str(idseq)} -> {str(idseq_temp)}')
                            idseq = idseq_temp
                    if sequences_pages.cur()[cdt]:
                        assert len(idseq) <= 2, f'{cdt} has pages but defines ids range of {len(idseq)} > 2!\n\tat line {i + 1}: {line}'
                    sequences_ids.cur()[cdt] = idseq
                    if len(idseq) < MIN_IDS_SEQ_LENGTH:
                        if cdt in Config.downloaders:
                            negative_str = ' NEGATIVE' if idseq[0] < 0 else ''
                            trace(f'{cdt} at line {i + 1:d} provides a single{negative_str} id hence requires maxid autoupdate')
                            if cat not in autoupdate_seqs:
                                autoupdate_seqs.add_category(cat)
                            autoupdate_seqs[cat][cdt] = idseq
                        else:
                            idseq.ints.append(2**31 - 1)
                elif re_pages_list.fullmatch(line):
                    cdt = cur_dl()
                    assert cdt in PAGE_DOWNLOADERS, f'{cdt} doesn\'t support pages search!\n\tat line {i + 1}: {line}'
                    idseq = sequences_ids.cur()[cdt]
                    if idseq:
                        assert len(idseq) <= 2, f'{cdt} defines pages but has ids range of {len(idseq)} > 2!\n\tat line {i + 1}: {line}'
                    pageseq = IntSequence([int(num[1:]) for num in line.split(' ')[1:]], i + 1)
                    sequences_pages.cur()[cdt] = pageseq
                    if len(pageseq) < MIN_IDS_SEQ_LENGTH:
                        pageseq.ints.append(1)
                elif re_downloader_basepath.fullmatch(line):
                    cdt = cur_dl()
                    basepath = line[line.find(':') + 1:]
                    basepath_n = normalize_path(basepath)
                    path_append = PATH_APPEND_DOWNLOAD_PAGES if sequences_pages.cur()[cdt] else PATH_APPEND_DOWNLOAD_IDS
                    path_downloader = f'{basepath_n}{path_append[cdt]}'
                    path_requirements = f'{basepath_n}{PATH_APPEND_REQUIREMENTS}'
                    path_updater = f'{basepath_n}{PATH_APPEND_UPDATE[cdt]}'
                    if Config.test is False:
                        assert path.isdir(basepath)
                        assert path.isfile(path_downloader)
                        if Config.install:
                            assert path.isfile(path_requirements)
                        if Config.update:
                            assert path.isfile(path_updater)
                    sequences_paths.cur()[cur_dl()] = path_downloader
                    sequences_paths_reqs[cur_dl()] = path_requirements
                    sequences_paths_update[cur_dl()] = normalize_path(path.abspath(path_updater), False)
                elif re_common_arg.fullmatch(line):
                    common_args = line[line.find(':') + 1:].split(' ')
                    proxy_idx = common_args.index(PROXY_ARG) if PROXY_ARG in common_args else -1
                    if proxy_idx >= 0:
                        assert len(common_args) > proxy_idx + 1
                        proxies_update[cur_dl()] = StrPair((common_args[proxy_idx], common_args[proxy_idx + 1]))
                    sequences_common.cur()[cur_dl()].extend(common_args)
                elif re_sub_begin.fullmatch(line):
                    cdt = cur_dl()
                    assert len(sequences_subfolders.cur()[cdt]) == len(sequences_tags.cur()[cdt]), f'Error: unclosed {cdt} sub!'
                    sequences_subfolders.cur()[cur_dl()].append(line[line.find(':') + 1:])
                elif re_sub_end.fullmatch(line):
                    sequences_tags.cur()[cur_dl()].append(cur_tags_list.copy())
                elif re_downloader_finalize.fullmatch(line):
                    cur_tags_list.clear()
                    cur_dwn = ''
                else:
                    trace(f'Error: unknown param at line {i + 1:d}!')
                    raise IOError
            else:  # elif line[0] in '(-*' or line[0].isalpha():
                assert sequences_ids.cur()[cur_dl()] or sequences_pages.cur()[cur_dl()]
                if '  ' in line:
                    trace(f'Error: double space found in tags at line {i + 1:d}!')
                    raise IOError
                if line[0] != '(' and not line.startswith('-+(') and '~' in line:
                    trace(f'Error: unsupported ungrouped OR symbol at line {i + 1:d}!')
                    raise IOError
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
                        assert len(tags_to_remove) == 0
                        continue
                    else:
                        tags_split = [tag[1:] for tag in line.split(' ')]
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
                            try_match_rem = split_len == 1 or cur_tag[::len(cur_tag) - 1] == '()'
                            if try_match_rem and cur_tag[start_idx:end_idx] == tags_rem:
                                del cur_tags_list[j]
                                need_find_previous_or_group = False
                                break
                        if need_find_previous_or_group is True:
                            trace(f'Info: exclusion(s) at {i + 1:d}, no previous matching tag or \'or\' group found. Line: \'{line}\'')
                elif not all_tags_positive(line.split(' ')):
                    param_like = line[0] == '-' and len(line.split(' ')) == 2
                    if not (param_like and (line.startswith('-search') or line.startswith('-quality'))):
                        trace(f'Warning (W2): mixed positive / negative tags at line {i + 1:d}, '
                              f'{"param" if param_like else "error"}? Line: \'{line}\'')
                if need_append:
                    cur_tags_list.extend(line.split(' '))
        except Exception as e:
            trace(f'Error: issue encountered while parsing queries file at line {i + 1:d}!\n - {str(e)}')
            raise

    trace('Sequences parsed successfully\n')
    if autoupdate_seqs:
        trace('[Autoupdate] validating runners...\n')
        validate_runners(sequences_paths, sequences_paths_reqs, sequences_paths_update)
        trace('Running max ID autoupdates...\n')
        unsolved_idseqs = list()
        needed_updates = [dt for dt in DOWNLOADERS if any(dt in autoupdate_seqs[c] for c in autoupdate_seqs if autoupdate_seqs[c][dt])]
        maxids = fetch_maxids(needed_updates)
        for dt in needed_updates:
            maxid = int(maxids[dt][4:])
            for cat in autoupdate_seqs:
                uidseq: IntSequence | None = autoupdate_seqs[cat][dt]
                if uidseq:
                    update_str_base = f'{cat}:{dt} id sequence extended from {str(uidseq.ints)} to '
                    if len(uidseq) == 1 and uidseq[0] < 0:
                        delta = uidseq.ints[0]
                        uidseq.ints.clear()
                        uidseq.ints.extend((maxid + delta, maxid))
                    else:
                        uidseq.ints.append(maxid)
                    trace(f'{update_str_base}{str(uidseq.ints)}')
                    maxid_fetched[dt] = maxid
        for cat in sequences_ids:
            for dt in sequences_ids[cat]:
                if sequences_ids[cat][dt] is not None and len(sequences_ids[cat][dt]) < MIN_IDS_SEQ_LENGTH:
                    unsolved_idseqs.append(f'{cat}:{dt}')
                    trace(f'{cat}:{dt} sequence is not fixed! \'{str(sequences_ids[cat][dt])}\'')
        assert len(unsolved_idseqs) == 0

    trace('Validating sequences...\n')
    validate_sequences(sequences_ids, sequences_pages, sequences_paths, sequences_tags, sequences_subfolders)
    if not autoupdate_seqs:
        validate_runners(sequences_paths, sequences_paths_reqs, sequences_paths_update)

    trace('Sequences validated. Finalizing...\n')
    queries_final = form_queries(sequences_ids, sequences_pages, sequences_paths, sequences_tags, sequences_subfolders, sequences_common)

    if Config.debug:
        trace('[DEBUG] Unoptimized:')
        report_unoptimized(sequences_ids, sequences_pages, sequences_paths, sequences_tags, sequences_subfolders, sequences_common)
        trace('\n\nFinals:')

    report_queries(queries_final)
    register_queries(queries_final)


def update_next_ids() -> None:
    if Config.update is False:
        trace('\nNext ids update SKIPPED due to no --update flag!')
        return

    # save backup and write a new one
    trace('\nNext ids update initiated...')

    queries_file_name = Config.script_path[Config.script_path.rfind(SLASH) + 1:]

    filename_bak = f'{queries_file_name}_bak_{datetime_str_nfull()}.list'
    trace(f'File: \'{queries_file_name}\', backup file: \'{filename_bak}\'')
    try:
        ids_downloaders = [dt for dt in Config.downloaders if any(sequences_ids[cat][dt] for cat in sequences_ids)]
        if ids_downloaders:
            [ids_downloaders.remove(dt) for dt in maxid_fetched if dt in ids_downloaders]
            results = fetch_maxids(ids_downloaders)
            trace(f'\nSaving backup to \'{filename_bak}\'...')
            bak_fullpath = f'{Config.dest_bak_base}{filename_bak}'
            with open(bak_fullpath, 'wt', encoding=UTF8, buffering=1) as outfile_bak:
                outfile_bak.writelines(queries_file_lines())
                trace('Saving done')

            trace(f'\nSetting read-only permissions for \'{filename_bak}\'...')
            perm = 0
            try:
                chmod(bak_fullpath, 0o100444)  # S_IFREG | S_IRUSR | S_IRGRP | S_IROTH
                perm = stat(bak_fullpath).st_mode
                assert (perm & 0o777) == 0o444
                trace('Permissions successfully updated')
            except AssertionError:
                trace(f'Warning: permissions mismatch \'{perm:o}\' != \'444\', manual fix required')
            except Exception:
                trace('Warning: permissions not updated, manual fix required')

            trace(f'\nWriting updated queries to \'{queries_file_name}\'...')
            maxids: dict[str, int] = {dt: int(results[dt][4:]) for dt in results}
            maxids.update(maxid_fetched)
            for dt in Config.update_offsets:
                uoffset = Config.update_offsets[dt]
                if dt in maxids:
                    maxids[dt] += uoffset
                    trace(f'Applying {dt.upper()} update offset {uoffset:d}: {maxids[dt] - uoffset:d} -> {maxids[dt]:d}')
                else:
                    trace(f'Warning: {dt.upper()} autoupdate offset ({uoffset:d}) was provided but its max id is not being updated')
            for cat in sequences_ids:
                i: int
                dtseq: tuple[str, IntSequence | None]
                for i, dtseq in enumerate(sequences_ids[cat].items()):
                    dt, seq = dtseq
                    line_n = (seq.line_num - 1) if seq and dt in maxids else None
                    trace(f'{"W" if line_n else "Not w"}riting \'{cat}:{dt}\' ids at idx {i:d}, line {line_n + 1 if line_n else -1:d}...')
                    if line_n:
                        ids_at_line = queries_file_lines()[line_n].strip().split(' ')
                        queries_file_lines()[line_n] = ' '.join([ids_at_line[0]] + ids_at_line[2:] + [f'{maxids[dt]:d}\n'])
                trace(f'Writing \'{cat}\' ids done')
            with open(Config.script_path, 'wt', encoding=UTF8, buffering=1) as outfile:
                outfile.writelines(queries_file_lines())
            trace('Writing done\n\nNext ids update successfully completed')
        else:
            trace('No id sequences were used, next ids update cancelled')
    except Exception:
        trace(f'\nError: failed to update next ids, you\'ll have to do it manually!! (backup has to be {filename_bak})\n')
        raise


def at_startup() -> None:
    trace(
        f'Python {sys.version}\nCommand-line args: {" ".join(sys.argv)}'
        f'\nEnabled downloaders: "{",".join(Config.downloaders) or "all"}"'
        f'\nEnabled categories: "{",".join(Config.categories) or "all"}"'
        f'\nIgnored arguments: {",".join(str(ign) for ign in Config.ignored_args) or "[]"}'
        f'\nIds overrides: {",".join(str(ove) for ove in Config.override_ids) or "[]"}'
    )

#
#
#########################################
