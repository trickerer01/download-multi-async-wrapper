# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import chmod, path, stat
from re import compile as re_compile
from subprocess import check_output
from threading import Thread, Lock as ThreadLock
from typing import List, Dict, Optional, Tuple, Iterable

from defs import (
    DownloadCollection, IntSequence, Config, StrPair, UTF8, DOWNLOADERS, MIN_IDS_SEQ_LENGTH, PATH_APPEND_DOWNLOAD_IDS,
    PATH_APPEND_DOWNLOAD_PAGES, PATH_APPEND_UPDATE, RUXX_DOWNLOADERS, PAGE_DOWNLOADERS, PROXY_ARG,
)
from executor import register_queries
from logger import trace
from sequences import validate_sequences, form_queries, report_finals, validate_runners
from strings import SLASH, NEWLINE, datetime_str_nfull, all_tags_negative, all_tags_positive, normalize_path

__all__ = ('read_queries_file', 'prepare_queries', 'update_next_ids')

re_category = re_compile(r'^### \(([A-zÀ-ʯА-я\d_+\-! ]+)\) ###$')
re_comment = re_compile(r'^##[^#].*?$')
re_download_mode = re_compile(r'^.*[: ]-dmode .+?$')
re_python_exec = re_compile(r'^### PYTHON:.*?$')
re_downloader_type = re_compile(fr'^# (?:{"|".join(DOWNLOADERS)}).*?$')
re_ids_list = re_compile(r'^#(?: \d+)+$')
re_pages_list = re_compile(r'^# p\d+(?: s\d+)?$')
re_downloader_basepath = re_compile(r'^# basepath:[A-Z/~].+?$')
re_common_arg = re_compile(r'^# common:-.+?$')
re_sub_begin = re_compile(r'^# sub:[^ ].*?$')
re_sub_end = re_compile(r'^# send$')
re_downloader_finalize = re_compile(r'^# end$')

queries_file_lines = list()  # type: List[str]

sequences_categories = list()  # type: List[str]
sequences_ids = list()  # type: List[DownloadCollection[IntSequence]]
sequences_pages = list()  # type: List[DownloadCollection[IntSequence]]
sequences_paths = list()  # type: List[DownloadCollection[str]]
sequences_common = list()  # type: List[DownloadCollection[List[str]]]
sequences_tags = list()  # type: List[DownloadCollection[List[List[str]]]]
sequences_subfolders = list()  # type: List[DownloadCollection[List[str]]]

sequences_paths_update = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[str]]
proxies_update = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[StrPair]]
maxid_fetched = dict()  # type: Dict[str, int]


def fetch_maxids(dts: Iterable[str]) -> Dict[str, str]:
    try:
        if not dts:
            return {}
        trace('Fetching max ids...')
        re_maxid_fetch_result = re_compile(r'^[A-Z]{2}: \d+$')
        grab_threads = []
        results = {dt: '' for dt in dts if sequences_paths_update[dt] is not None}  # type: Dict[str, str]
        rlock = ThreadLock()

        def get_max_id(dtype: str) -> None:
            update_file_path = sequences_paths_update[dtype]
            module_arguments = ['-module', dtype, '-timeout', '30'] if dtype in RUXX_DOWNLOADERS else ([''] * 0)
            if dtype in proxies_update and proxies_update[dtype]:
                module_arguments += [proxies_update[dtype].first, proxies_update[dtype].second]
            arguments = [Config.python, update_file_path, '-get_maxid'] + module_arguments
            res = check_output(arguments.copy()).decode(errors='replace').strip()
            with rlock:
                results[dtype] = res[res.rfind('\n') + 1:]

        for dt in results:
            grab_threads.append(Thread(target=get_max_id, args=(dt,)))
            grab_threads[-1].start()
        for thread in grab_threads:
            thread.join()
        res_errors = list()
        for dt in results:
            try:
                assert re_maxid_fetch_result.fullmatch(results[dt])
            except Exception:
                res_errors.append(f'Error in fetch \'{dt}\' max id result!')
                continue
        assert len(res_errors) == 0

        trace(NEWLINE.join(results[dt] for dt in results))
        return results
    except Exception:
        trace('\nError: failed to fetch next ids!\n')
        raise


def read_queries_file() -> None:
    global queries_file_lines

    with open(Config.script_path, 'rt', encoding=UTF8) as qfile:
        queries_file_lines = qfile.readlines()


def prepare_queries() -> None:
    def cur_dl() -> str:
        try:
            assert sequences_categories
        except AssertionError:
            trace(f'\nat line {i + 1:d}: current download category isn\'t selected!')
            raise
        try:
            assert cur_dwn
            return cur_dwn
        except AssertionError:
            trace(f'\nat line {i + 1:d}: current downloader isn\'t selected!')
            raise

    cur_dwn = ''
    cur_tags_list = list()  # type: List[str]
    autoupdate_seqs = dict()  # type: Dict[str, List[IntSequence]]

    trace('\nAnalyzing queries file strings...')

    for i, line in enumerate(queries_file_lines):
        try:
            line = line.strip(' \n\ufeff')  # remove BOM too
            if line == '':
                continue
            if line.startswith('###'):
                if re_python_exec.fullmatch(line):
                    assert Config.python == '', 'Python executable must be declared exactly once!'
                    Config.python = line[line.find(':') + 1:]
                    continue
                cat_match = re_category.fullmatch(line)
                assert cat_match, f'at line {i + 1:d}: invalid category header format: \'{line}\'!'
                cur_cat = cat_match.group(1)[:3].strip()
                trace(f'Processing new category: \'{cur_cat}\'...')
                sequences_categories.append(cur_cat)
                sequences_ids.append(DownloadCollection(cur_cat))
                sequences_pages.append(DownloadCollection(cur_cat))
                sequences_paths.append(DownloadCollection(cur_cat))
                sequences_common.append(DownloadCollection(cur_cat, []))
                sequences_tags.append(DownloadCollection(cur_cat, []))
                sequences_subfolders.append(DownloadCollection(cur_cat, []))
                cur_tags_list.clear()
                continue
            if line[0] not in '(-*#' and not line[0].isalpha():
                trace(f'Error: corrupted line beginning found at line {i + 1:d}!')
                raise IOError
            if line.startswith('#'):
                if re_comment.fullmatch(line):
                    # trace(f'Ignoring commented out line {i + 1:d}: \'{line}\'')
                    continue
                if re_download_mode.fullmatch(line):
                    if Config.ignore_download_mode is True:
                        trace(f'Info: \'{line}\' download mode found at line {i + 1:d}. Ignored!')
                        continue
                if re_downloader_type.fullmatch(line):
                    cur_dwn = line.split(' ')[1]
                    assert cur_dwn in DOWNLOADERS
                    trace(f'Processing \'{cur_dl().upper()}\' arguments...')
                elif re_ids_list.fullmatch(line):
                    cdt = cur_dl()
                    idseq = IntSequence([int(num) for num in line.split(' ')[1:]], i + 1)
                    if sequences_pages[-1][cdt]:
                        assert len(idseq) <= 2, f'{cdt} has pages but defines ids range of {len(idseq)} > 2!\n\tat line {i + 1}: {line}'
                    sequences_ids[-1][cdt] = idseq
                    if len(idseq) < MIN_IDS_SEQ_LENGTH:
                        if cdt in Config.downloaders:
                            trace(f'{cdt} at line {i + 1:d} provides a single id hence requires maxid autoupdate')
                            if cdt not in autoupdate_seqs:
                                autoupdate_seqs[cdt] = list()
                            autoupdate_seqs[cdt].append(idseq)
                        else:
                            idseq.ints.append(2**31 - 1)
                elif re_pages_list.fullmatch(line):
                    cdt = cur_dl()
                    assert cdt in PAGE_DOWNLOADERS, f'{cdt} doesn\'t support pages search!\n\tat line {i + 1}: {line}'
                    idseq = sequences_ids[-1][cdt]
                    if idseq:
                        assert len(idseq) <= 2, f'{cdt} defines pages but has ids range of {len(idseq)} > 2!\n\tat line {i + 1}: {line}'
                    pageseq = IntSequence([int(num[1:]) for num in line.split(' ')[1:]], i + 1)
                    sequences_pages[-1][cdt] = pageseq
                    if len(pageseq) < MIN_IDS_SEQ_LENGTH:
                        pageseq.ints.append(1)
                elif re_downloader_basepath.fullmatch(line):
                    cdt = cur_dl()
                    basepath = line[line.find(':') + 1:]
                    basepath_n = normalize_path(basepath)
                    path_append = PATH_APPEND_DOWNLOAD_PAGES if sequences_pages[-1][cdt] else PATH_APPEND_DOWNLOAD_IDS
                    path_downloader = f'{basepath_n}{path_append[cdt]}'
                    path_updater = f'{basepath_n}{PATH_APPEND_UPDATE[cdt]}'
                    if Config.test is False:
                        assert path.isdir(basepath)
                        assert path.isfile(path_downloader)
                        if Config.update:
                            assert path.isfile(path_updater)
                    sequences_paths[-1][cur_dl()] = path_downloader
                    sequences_paths_update[cur_dl()] = normalize_path(path.abspath(path_updater), False)
                elif re_common_arg.fullmatch(line):
                    common_args = line[line.find(':') + 1:].split(' ')
                    proxy_idx = common_args.index(PROXY_ARG) if PROXY_ARG in common_args else -1
                    if proxy_idx >= 0:
                        assert len(common_args) > proxy_idx + 1
                        proxies_update[cur_dl()] = StrPair((common_args[proxy_idx], common_args[proxy_idx + 1]))
                    sequences_common[-1][cur_dl()] += common_args
                elif re_sub_begin.fullmatch(line):
                    sequences_subfolders[-1][cur_dl()].append(line[line.find(':') + 1:])
                elif re_sub_end.fullmatch(line):
                    sequences_tags[-1][cur_dl()].append(cur_tags_list.copy())
                elif re_downloader_finalize.fullmatch(line):
                    cur_tags_list.clear()
                    cur_dwn = ''
                else:
                    trace(f'Error: unknown param at line {i + 1:d}!')
                    raise IOError
            else:  # elif line[0] in '(-*' or line[0].isalpha():
                assert sequences_ids[-1][cur_dl()] or sequences_pages[-1][cur_dl()]
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
                        for j in reversed(range(len(cur_tags_list))):  # type: int
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
                    cur_tags_list += line.split(' ')
        except Exception:
            trace(f'Error: issue encountered while parsing queries file at line {i + 1:d}!')
            raise

    trace('Sequences parsed successfully\n')
    if autoupdate_seqs:
        trace('[Autoupdate] validating runners...\n')
        validate_runners(sequences_paths, sequences_paths_update)
        trace('Running max ID autoupdates...\n')
        unsolved_idseqs = [''] * 0
        maxids = fetch_maxids(dt for dt in autoupdate_seqs)
        for dt in autoupdate_seqs:
            for uidseq in autoupdate_seqs[dt]:
                update_str_base = f'{dt} id sequence extended from {str(uidseq.ints)} to '
                maxid = int(maxids[dt][4:])
                uidseq.ints.append(maxid)
                trace(f'{update_str_base}{str(uidseq.ints)}')
                maxid_fetched[dt] = maxid
        for cat, sidseq in zip(sequences_categories, sequences_ids):
            for dt in sidseq.dls:
                if sidseq.dls[dt] is not None and len(sidseq.dls[dt]) < MIN_IDS_SEQ_LENGTH:
                    unsolved_idseqs.append(f'{cat}:{dt}')
                    trace(f'{cat}:{dt} sequence is not fixed! \'{str(sidseq.dls[dt])}\'')
        assert len(unsolved_idseqs) == 0

    trace('Validating sequences...\n')
    validate_sequences(sequences_ids, sequences_pages, sequences_paths, sequences_tags, sequences_subfolders)
    if not autoupdate_seqs:
        validate_runners(sequences_paths, sequences_paths_update)

    trace('Sequences validated. Finalizing...\n')
    queries_final = form_queries(sequences_ids, sequences_pages, sequences_paths, sequences_tags, sequences_subfolders, sequences_common)

    report_finals(queries_final, sequences_categories)
    register_queries(queries_final, sequences_categories)


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
        ids_downloaders = [dt for dt in Config.downloaders if any(idseq.dls[dt] for idseq in sequences_ids)]
        if ids_downloaders:
            [ids_downloaders.remove(dt) for dt in maxid_fetched if dt in ids_downloaders]
            results = fetch_maxids(ids_downloaders)
            trace(f'\nSaving backup to \'{filename_bak}\'...')
            bak_fullpath = f'{Config.dest_bak_base}{filename_bak}'
            with open(bak_fullpath, 'wt', encoding=UTF8, buffering=1) as outfile_bak:
                outfile_bak.writelines(queries_file_lines)
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
            maxids = {dt: int(results[dt][4:]) for dt in results}  # type: Dict[str, int]
            maxids.update(maxid_fetched)
            for idseq in sequences_ids:
                ty = idseq.name
                for i, dtseq in enumerate(idseq.dls.items()):  # type: int, Tuple[str, Optional[IntSequence]]
                    dt, seq = dtseq
                    line_n = (seq.line_num - 1) if seq and dt in maxids else None
                    trace(f'{"W" if line_n else "Not w"}riting {ty} {dt} ids at idx {i:d}, line {line_n + 1 if line_n else -1:d}...')
                    if line_n:
                        delta = 1 * int(not not [seqp.dls[dt] for seqp in sequences_pages if ty == seqp.name])
                        ids_at_line = queries_file_lines[line_n].strip().split(' ')
                        queries_file_lines[line_n] = ' '.join([ids_at_line[0]] + ids_at_line[2:] + [f'{maxids[dt] + delta:d}\n'])
                trace(f'Writing {ty} ids done')
            with open(Config.script_path, 'wt', encoding=UTF8, buffering=1) as outfile:
                outfile.writelines(queries_file_lines)
            trace('Writing done\n\nNext ids update successfully completed')
        else:
            trace('No id sequences were used, next ids update cancelled')
    except Exception:
        trace(f'\nError: failed to update next ids, you\'ll have to do it manually!! (backup has to be {filename_bak})\n')
        raise

#
#
#########################################
