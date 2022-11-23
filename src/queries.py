# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

# from subprocess import call as call_subprocess
from os import chmod, stat
from re import fullmatch
from subprocess import check_output
from typing import List, Dict, Optional, Tuple

from defs import DOWNLOADERS, UTF8, Sequence, Config
from executor import register_vid_queries, register_img_queries
from logger import trace
from sequences import validate_sequences, report_sequences, queries_from_sequences, report_finals
from strings import datetime_str_nfull, bytes_to_lines, all_tags_negative, SLASH, NEWLINE

queries_file_lines = []  # type: List[str]

sequences_ids_vid = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[Sequence]]
sequences_ids_img = {dt: None for dt in DOWNLOADERS}  # type: Dict[str, Optional[Sequence]]


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
    cur_tags_list = []  # type: List[str]

    trace('\nAnalyzing queries file strings...')

    for i, line in enumerate(queries_file_lines):
        try:
            line = line.strip()
            if i == 0 or line in ['', '### (VIDEOS) ###', '### (IMAGES) ###']:
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
            if line[0] not in ['(', '-', '*', '#'] and not line[0].isalpha():
                trace(f'Error: corrupted line beginning found at line {i + 1:d}!')
                raise IOError
            if line[0] == '#':
                if fullmatch(r'^##.*?$', line):
                    trace(f'Ignoring commented out line {i + 1:d}: \'{line}\'')
                    continue
                if fullmatch(r'^.*[: ]-dmode .+?$', line):
                    if Config.ignore_download_mode is True:
                        trace(f'Info: \'{line}\' download mode found at line {i + 1:d}. Ignored!')
                        continue
                if fullmatch(fr'^# (?:{"|".join(DOWNLOADERS)}).*?$', line):
                    cur_downloader_idx = DOWNLOADERS.index(line.split(' ')[1])
                elif fullmatch(r'^#(?: \d+)+$', line):
                    cur_seq_ids[DOWNLOADERS[cur_downloader_idx]] = Sequence([int(num) for num in line.split(' ')[1:]], i + 1)
                elif fullmatch(r'^# path:[A-Z/~].+?$', line):
                    cur_seq_paths[DOWNLOADERS[cur_downloader_idx]] = line[line.find(':') + 1:]
                elif fullmatch(r'^# common:-.+?$', line):
                    cur_seq_common[DOWNLOADERS[cur_downloader_idx]] += line[line.find(':') + 1:].split(' ')
                elif fullmatch(r'^# sub:[^ ].*?$', line):
                    cur_seq_subs[DOWNLOADERS[cur_downloader_idx]].append(line[line.find(':') + 1:])
                elif fullmatch(r'^# send$', line):
                    cur_seq_tags[DOWNLOADERS[cur_downloader_idx]].append(cur_tags_list.copy())
                elif fullmatch(r'^# end$', line):
                    cur_tags_list.clear()
                else:
                    trace(f'Error: unknown param at line {i + 1:d}!')
                    raise IOError
            else:  # elif line[0] in ['(', '-', '*'] or line[0].isalpha():
                assert len(cur_seq_ids[DOWNLOADERS[cur_downloader_idx]].ids) > 0
                if line[0] not in ['('] and (not line.startswith('-+(')) and line.find('~') != -1:
                    trace(f'Error: unsupported ungrouped OR symbol at line {i + 1:d}!')
                    raise IOError
                if all_tags_negative(line.split(' ')):
                    if line[1] in ['-', '+']:
                        # remove --tag(s) or -+tag(s) from list, convert: --a --b -> [-a, -b] OR -+a -+b -> [a, b]
                        tags_to_remove = [tag[2 if line[1] == '+' else 1:] for tag in line.split(' ')]
                        for k in reversed(range(len(tags_to_remove))):
                            for j in reversed(range(len(cur_tags_list))):
                                if cur_tags_list[j] == tags_to_remove[k]:
                                    del cur_tags_list[j]
                                    del tags_to_remove[k]
                                    break
                        assert len(tags_to_remove) == 0
                        continue
                    else:
                        for j in reversed(range(len(cur_tags_list))):
                            if cur_tags_list[j][0] == '(' and cur_tags_list[j][-1] == ')' and cur_tags_list[j].find('~') != -1:
                                assert cur_tags_list[j][1:-1] == '~'.join(tag[1:] for tag in line.split(' '))
                                del cur_tags_list[j]
                                break
                cur_tags_list += line.split(' ')
        except Exception:
            trace(f'Error: issue encountered while parsing queries file at line {i + 1:d}!')
            raise

    trace('Sequences are successfully read\n')
    report_sequences(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
                     sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
                     sequences_common_vid, sequences_common_img)
    validate_sequences(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
                       sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img)

    trace('Sequences are validated. Preparing final lists...')
    queries_final_vid, queries_final_img = queries_from_sequences(
        sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
        sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img,
        sequences_common_vid, sequences_common_img
    )

    report_finals(queries_final_vid, queries_final_img)

    register_vid_queries(queries_final_vid)
    register_img_queries(queries_final_img)


def update_next_ids() -> None:
    if Config.update is False:
        return

    # save backup and write a new one
    trace('\nNext ids update initiated...')

    queries_file_name = Config.script_path[Config.script_path.rfind(SLASH) + 1:]

    filename_bak = f'{queries_file_name}_bak_{datetime_str_nfull()}.list'
    trace(f'File: \'{queries_file_name}\', backup file: \'{filename_bak}\'')
    try:
        trace('Fetching max ids...')
        # b'NM: 71773\r\nRN: 526263\r\nRV: 3090582\r\nRX: 6867121\r\n\r\n'
        fetch_result = check_output(['python3', f'{Config.fetcher_root}main.py', '--silent'])
        trace(f'\nFetch max ids output (bytes): \'{str(fetch_result)}\'')

        lines = bytes_to_lines(fetch_result)[:4]
        trace(NEWLINE.join(lines))

        trace(f'\nSaving backup to \'{filename_bak}\'...')
        bak_fullpath = f'{Config.dest_bak_base}{filename_bak}'
        with open(bak_fullpath, 'wt', encoding=UTF8, buffering=True) as outfile_bak:
            outfile_bak.writelines(queries_file_lines)
            trace('Saving done')

        trace(f'\nUpdating permissions for \'{filename_bak}\'...')
        perm = 0
        try:
            chmod(bak_fullpath, 0o100444)  # S_IFREG | S_IRUSR | S_IRGRP | S_IROTH
            perm = stat(bak_fullpath).st_mode
            assert (perm & 0o777) == 0o444
            trace('Permissions successfully updated')
        except AssertionError:
            trace(f'Warning: permissions mismatch \'{"%o" % perm}\' != \'444\', manual fix required')
        except Exception:
            trace('Warning: permissions not updated, manual fix required')

        trace(f'\nWriting updated queries to \'{queries_file_name}\'...')
        maxnums = {dt: num for dt, num in [(line[:2].lower(), int(line[4:])) for line in lines]}  # type: Dict[str, int]
        for ty, sequences_ids_type in zip(['vid', 'img'], [sequences_ids_vid, sequences_ids_img]):
            for i, dtseq in enumerate(sequences_ids_type.items()):  # type: int, Tuple[str, Optional[Sequence]]
                dt, seq = dtseq
                line_num = (seq.line_num - 1) if seq else None
                trace(f'{"W" if line_num else "Not w"}riting {dt} {ty} ids at idx {i:d}, line {line_num + 1 if line_num else -1:d}...')
                if line_num:
                    ids_at_line = queries_file_lines[line_num].strip().split(' ')
                    queries_file_lines[line_num] = ' '.join([ids_at_line[0]] + ids_at_line[2:] + [f'{maxnums[dt]:d}\n'])
                    trace(f'Writing {dt} {ty} ids done')
            trace(f'Writing {ty} ids done')
        with open(Config.script_path, 'wt', encoding=UTF8, buffering=True) as outfile:
            outfile.writelines(queries_file_lines)
        trace('Writing done')
    except Exception:
        trace(f'\nError: failed to update next ids, you\'ll have to do it manually!! (backup has to be {filename_bak})\n')
        raise

    trace('\nNext ids update successfully completed')

#
#
#########################################
