# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

# from subprocess import call as call_subprocess
from os import chmod, path, stat
from re import compile as re_compile
from subprocess import check_output
from threading import Thread, Lock as ThreadLock
from typing import List, Dict, Optional, Tuple, Iterable

from defs import (
    IntSequence, Config, StrPair, UTF8, DOWNLOADERS, MIN_IDS_SEQ_LENGTH, PATH_APPEND_DOWNLOAD, PATH_APPEND_UPDATE, RUXX_DOWNLOADERS,
    PROXY_ARG,
)
from executor import register_queries
from logger import trace
from sequences import validate_sequences, queries_from_sequences, report_finals  # , report_sequences, queries_from_sequences_base
from strings import SLASH, NEWLINE, datetime_str_nfull, all_tags_negative, all_tags_positive, normalize_path

__all__ = ('read_queries_file', 'form_queries', 'update_next_ids')

re_comment = re_compile(r'^##[^#].*?$')
re_download_mode = re_compile(r'^.*[: ]-dmode .+?$')
re_python_exec = re_compile(r'^### PYTHON:.*?$')
re_downloader_type = re_compile(fr'^# (?:{"|".join(DOWNLOADERS)}).*?$')
re_ids_list = re_compile(r'^#(?: \d+)+$')
re_downloader_basepath = re_compile(r'^# basepath:[A-Z/~].+?$')
re_common_arg = re_compile(r'^# common:-.+?$')
re_sub_begin = re_compile(r'^# sub:[^ ].*?$')
re_sub_end = re_compile(r'^# send$')
re_downloader_finilize = re_compile(r'^# end$')

queries_file_lines = []  # type: List[str]

sequences_ids_vid = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[IntSequence]]
sequences_ids_img = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[IntSequence]]

sequences_paths_update = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[str]]
proxies_update = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[StrPair]]


def fetch_maxids(dts: Iterable[str]) -> Dict[str, str]:
    try:
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
        trace(f'\nError: failed to fetch next ids!\n')
        raise


def read_queries_file() -> None:
    global queries_file_lines

    with open(Config.script_path, 'rt', encoding=UTF8) as qfile:
        queries_file_lines = qfile.readlines()


def form_queries():
    sequences_paths_vid = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[str]]
    sequences_paths_img = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[str]]
    sequences_common_vid = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]
    sequences_common_img = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]
    sequences_tags_vid = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[List[str]]]
    sequences_tags_img = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[List[str]]]
    sequences_subfolders_vid = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]
    sequences_subfolders_img = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]

    cur_downloader_idx = 0
    cur_seq_ids = sequences_ids_vid
    cur_seq_paths = sequences_paths_vid
    cur_seq_common = sequences_common_vid
    cur_seq_tags = sequences_tags_vid
    cur_seq_subs = sequences_subfolders_vid
    cur_tags_list = list()  # type: List[str]

    autoupdate_seqs = dict()  # type: Dict[str, List[IntSequence]]

    trace('\nAnalyzing queries file strings...')

    for i, line in enumerate(queries_file_lines):
        try:
            line = line.strip(' \n\ufeff')  # remove BOM too
            if line in ('', '### (VIDEOS) ###', '### (IMAGES) ###'):
                if line == '### (VIDEOS) ###':
                    cur_seq_ids = sequences_ids_vid
                    cur_seq_paths = sequences_paths_vid
                    cur_seq_common = sequences_common_vid
                    cur_seq_tags = sequences_tags_vid
                    cur_seq_subs = sequences_subfolders_vid
                    cur_tags_list.clear()
                elif line == '### (IMAGES) ###':
                    cur_seq_ids = sequences_ids_img
                    cur_seq_paths = sequences_paths_img
                    cur_seq_common = sequences_common_img
                    cur_seq_tags = sequences_tags_img
                    cur_seq_subs = sequences_subfolders_img
                    cur_tags_list.clear()
                continue
            if line[0] not in '(-*#' and not line[0].isalpha():
                trace(f'Error: corrupted line beginning found at line {i + 1:d}!')
                raise IOError
            if line[0] == '#':
                if re_comment.fullmatch(line):
                    # trace(f'Ignoring commented out line {i + 1:d}: \'{line}\'')
                    continue
                if re_download_mode.fullmatch(line):
                    if Config.ignore_download_mode is True:
                        trace(f'Info: \'{line}\' download mode found at line {i + 1:d}. Ignored!')
                        continue
                if re_python_exec.fullmatch(line):
                    assert Config.python == '', 'Python executable must be declared exactly once!'
                    Config.python = line[line.find(':') + 1:]
                elif re_downloader_type.fullmatch(line):
                    cur_downloader_idx = DOWNLOADERS.index(line.split(' ')[1])
                elif re_ids_list.fullmatch(line):
                    cdt = DOWNLOADERS[cur_downloader_idx]
                    idseq = IntSequence([int(num) for num in line.split(' ')[1:]], i + 1)
                    cur_seq_ids[cdt] = idseq
                    if len(idseq) < MIN_IDS_SEQ_LENGTH:
                        trace(f'{cdt} at line {i + 1:d} provides a single id hence requires maxid autoupdate')
                        if cdt not in autoupdate_seqs:
                            autoupdate_seqs[cdt] = list()
                        autoupdate_seqs[cdt].append(idseq)
                elif re_downloader_basepath.fullmatch(line):
                    basepath = line[line.find(':') + 1:]
                    basepath_n = normalize_path(basepath)
                    path_downloader = f'{basepath_n}{PATH_APPEND_DOWNLOAD[DOWNLOADERS[cur_downloader_idx]]}'
                    path_updater = f'{basepath_n}{PATH_APPEND_UPDATE[DOWNLOADERS[cur_downloader_idx]]}'
                    if Config.test is False:
                        assert path.isdir(basepath)
                        assert path.isfile(path_downloader)
                        if Config.update:
                            assert path.isfile(path_updater)
                    cur_seq_paths[DOWNLOADERS[cur_downloader_idx]] = path_downloader
                    sequences_paths_update[DOWNLOADERS[cur_downloader_idx]] = normalize_path(path.abspath(path_updater), False)
                elif re_common_arg.fullmatch(line):
                    common_args = line[line.find(':') + 1:].split(' ')
                    proxy_idx = common_args.index(PROXY_ARG) if PROXY_ARG in common_args else -1
                    if proxy_idx >= 0:
                        assert len(common_args) > proxy_idx + 1
                        proxies_update[DOWNLOADERS[cur_downloader_idx]] = StrPair((common_args[proxy_idx], common_args[proxy_idx + 1]))
                    cur_seq_common[DOWNLOADERS[cur_downloader_idx]] += common_args
                elif re_sub_begin.fullmatch(line):
                    cur_seq_subs[DOWNLOADERS[cur_downloader_idx]].append(line[line.find(':') + 1:])
                elif re_sub_end.fullmatch(line):
                    cur_seq_tags[DOWNLOADERS[cur_downloader_idx]].append(cur_tags_list.copy())
                elif re_downloader_finilize.fullmatch(line):
                    cur_tags_list.clear()
                else:
                    trace(f'Error: unknown param at line {i + 1:d}!')
                    raise IOError
            else:  # elif line[0] in '(-*' or line[0].isalpha():
                assert len(cur_seq_ids[DOWNLOADERS[cur_downloader_idx]]) > 0
                if '  ' in line:
                    trace(f'Error: double space found in tags at line {i + 1:d}!')
                    raise IOError
                if line[0] != '(' and not line.startswith('-+(') and '~' in line:
                    trace(f'Error: unsupported ungrouped OR symbol at line {i + 1:d}!')
                    raise IOError
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
                        start_idx = 1 if split_len > 1 else 0  # type: int
                        end_idx = -1 if split_len > 1 else None  # type: Optional[int]
                        for j in reversed(range(len(cur_tags_list))):  # type: int
                            border_condition = split_len == 1 or cur_tags_list[j][:: len(cur_tags_list[j]) - 1] == '()'
                            if border_condition and cur_tags_list[j][start_idx:end_idx] == tags_rem:
                                del cur_tags_list[j]
                                need_find_previous_or_group = False
                                break
                        if need_find_previous_or_group is True:
                            trace(f'Info: exclusion(s) at {i + 1:d}, no previous matching tag or \'or\' group found. Line: \'{line}\'')
                elif not all_tags_positive(line.split(' ')):
                    param_like = line[0] == '-' and len(line.split(' ')) == 2
                    trace(f'Warning (W2): mixed positive / negative tags at line {i + 1:d}, '
                          f'{"param" if param_like else "error"}? Line: \'{line}\'')
                cur_tags_list += line.split(' ')
        except Exception:
            trace(f'Error: issue encountered while parsing queries file at line {i + 1:d}!')
            raise

    if autoupdate_seqs:
        trace(f'Running max ID autoupdates...')
        unsolved_idseqs_vid = [''] * 0
        unsolved_idseqs_img = [''] * 0
        maxids = fetch_maxids(dt for dt in autoupdate_seqs)
        for dt in autoupdate_seqs:
            for idseq in autoupdate_seqs[dt]:
                update_str_base = f'{dt} id sequence autoupdated from {str(idseq.ids)} to '
                idseq.ids.append(int(maxids[dt][4:]))
                trace(f'{update_str_base}{str(idseq.ids)}')
        for typ, idseq, usiseq in zip(('vid', 'img'), (sequences_ids_vid, sequences_ids_img), (unsolved_idseqs_vid, unsolved_idseqs_img)):
            for dt in idseq:
                if idseq[dt] is not None and len(idseq[dt]) < MIN_IDS_SEQ_LENGTH:
                    usiseq.append(f'{dt}')
                    trace(f'{dt} {typ} sequence is not fixed! \'{str(idseq[dt])}\'')
        assert all(len(usiseq) == 0 for usiseq in (unsolved_idseqs_vid, unsolved_idseqs_img))

    trace('Sequences are successfully read\n')
    # report_sequences(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
    #                  sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
    #                  sequences_common_vid, sequences_common_img,
    #                  python_executable)
    validate_sequences(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
                       sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
                       sequences_paths_update)

    trace('Sequences are validated. Preparing final lists...')

    # base final sequences
    # trace('\nBase:')
    # report_finals(*queries_from_sequences_base(
    #     sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
    #     sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
    #     sequences_common_vid, sequences_common_img
    # ))

    trace('\nOptimized:')
    queries_final_vid, queries_final_img = queries_from_sequences(
        sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
        sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
        sequences_common_vid, sequences_common_img
    )

    report_finals(queries_final_vid, queries_final_img)
    register_queries(queries_final_vid, queries_final_img)


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
        results = fetch_maxids(Config.downloaders)
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
        maxnums = {dt: int(results[dt][4:]) for dt in results}  # type: Dict[str, int]
        for ty, sequences_ids_type in zip(('vid', 'img'), (sequences_ids_vid, sequences_ids_img)):
            for i, dtseq in enumerate(sequences_ids_type.items()):  # type: int, Tuple[str, Optional[IntSequence]]
                dt, seq = dtseq
                line_num = (seq.line_num - 1) if seq and dt in maxnums else None
                trace(f'{"W" if line_num else "Not w"}riting {dt} {ty} ids at idx {i:d}, line {line_num + 1 if line_num else -1:d}...')
                if line_num:
                    ids_at_line = queries_file_lines[line_num].strip().split(' ')
                    queries_file_lines[line_num] = ' '.join([ids_at_line[0]] + ids_at_line[2:] + [f'{maxnums[dt]:d}\n'])
                    trace(f'Writing {dt} {ty} ids done')
            trace(f'Writing {ty} ids done')
        with open(Config.script_path, 'wt', encoding=UTF8, buffering=1) as outfile:
            outfile.writelines(queries_file_lines)
        trace('Writing done')
    except Exception:
        trace(f'\nError: failed to update next ids, you\'ll have to do it manually!! (backup has to be {filename_bak})\n')
        raise

    trace('\nNext ids update successfully completed')

#
#
#########################################
