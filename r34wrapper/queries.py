# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from collections.abc import Iterable
from subprocess import CalledProcessError, check_output
from threading import Lock, Thread

from .config import Config
from .defs import (
    COLOR_LOG_DOWNLOADERS,
    DOWNLOADERS,
    MIN_IDS_SEQ_LENGTH,
    PAGE_DOWNLOADERS,
    RUXX_DOWNLOADERS,
    UTF8,
    IntSequence,
)
from .executor import register_queries
from .logger import trace
from .parsers import create_parser
from .sequences import form_queries, report_queries, report_unoptimized, validate_runners, validate_sequences
from .strings import NEWLINE, SLASH, datetime_str_nfull

__all__ = ('make_parser', 'prepare_queries', 'read_queries_file', 'update_next_ids')


class MaxIdFetchContext:
    CONTEXT_PREFETCH = 1
    CONTEXT_AUTOUPDATE = 2
    CONTEXT_UPDATE_NEXT = 3


def fetch_maxids_if_needed(*, context: int) -> None:
    is_context_prefetch = context == MaxIdFetchContext.CONTEXT_PREFETCH
    if is_context_prefetch and not Config.update_prefetch:
        return

    queries = Config.parser.queries
    autoupdate_seqs = queries.autoupdate_seqs
    needed_autoupdates = [dt for dt in DOWNLOADERS if any(dt in autoupdate_seqs[c] for c in autoupdate_seqs if autoupdate_seqs[c][dt])
                          and dt not in Config.fetched_maxids] if autoupdate_seqs else [''] * 0
    ids_downloaders = [dt for dt in Config.downloaders if any(queries.sequences_ids[cat][dt] for cat in queries.sequences_ids)
                       and dt not in Config.fetched_maxids] if Config.update else [''] * 0

    if bool(needed_autoupdates or ids_downloaders):
        if is_context_prefetch:
            trace('Max id fetch was triggered by prefetcher!')
        validate_runners(queries)
        fetch_maxids(set(needed_autoupdates).union(ids_downloaders))


def fetch_maxids(dts: Iterable[str]) -> None:
    try:
        if not dts:
            return
        trace('Fetching max ids...')
        queries = Config.parser.queries
        grab_threads: list[Thread] = []
        results: dict[str, str] = {dt: '' for dt in dts if queries.sequences_paths_update[dt] is not None}
        rlock = Lock()

        if Config.test:
            Config.fetched_maxids.update(dict.fromkeys(results, f'{10 ** 18:d}'))
            return

        def get_max_id(dtype: str) -> None:
            update_file_path: str = queries.sequences_paths_update[dtype]
            module_arguments: list[str] = ['-module', dtype] if dtype in RUXX_DOWNLOADERS else []
            if dtype in PAGE_DOWNLOADERS:
                module_arguments.append('pages')
            if dtype in COLOR_LOG_DOWNLOADERS:
                module_arguments.append('--disable-log-colors')
            if dtype in queries.proxies_update and queries.proxies_update[dtype] and dtype not in Config.noproxy_fetches:
                if queries.proxies_update[dtype].second:
                    module_arguments.extend((queries.proxies_update[dtype].first, queries.proxies_update[dtype].second))
            for extra_args in Config.extra_args:
                if extra_args.is_for(queries.sequences_common.cur_cat, dtype):
                    module_arguments.extend(extra_args.args)
            arguments = [Config.python, update_file_path, *module_arguments, '-get_maxid', '-timeout', '20', '-retries', '1']
            try:
                trace(f'Executing "{" ".join(arguments)}"...')
                res = check_output(arguments).decode(errors='replace').strip()
                # DEBUG: do not remove
                # trace(f'Output of {dtype.upper()}: {res}')
            except (KeyboardInterrupt, CalledProcessError):
                res = 'ERROR'
            with rlock:
                results[dtype] = res[res.rfind('\n') + 1:][4:]  # "RV: 1234567"

        for dt in results:
            grab_threads.append(Thread(target=get_max_id, args=(dt,)))
            grab_threads[-1].start()
        while grab_threads:
            thread = grab_threads.pop(-1)
            if thread.is_alive():
                try:
                    thread.join()
                except KeyboardInterrupt:
                    pass
        res_errors: list[str] = []
        for dt, result in results.items():
            try:
                assert result.isnumeric()
            except AssertionError:
                res_errors.append(f'Error in fetch \'{dt}\' max id result!')
                continue
        assert len(res_errors) == 0, '\n ' + '\n '.join(res_errors)

        trace(NEWLINE.join(f'{dt.upper()}: {id_str}' for dt, id_str in results.items()))
        Config.fetched_maxids.update(results)
    except AssertionError:
        trace('\nError: failed to fetch next ids!\n')
        raise


def make_parser() -> None:
    assert Config.test or Config.parser is None, 'Error: make_parser() should only be called once'
    Config.parser = create_parser()


def read_queries_file() -> None:
    trace(f'\nReading queries file: \'{Config.script_path}\'')
    with open(Config.script_path, 'rt', encoding=UTF8) as qfile:
        Config.parser.queries.queries_file_lines[:] = qfile.readlines()


def run_autoupdates() -> None:
    trace('Running max ID autoupdates...\n')
    queries = Config.parser.queries
    unsolved_idseqs: list[str] = []
    autoupdate_seqs = queries.autoupdate_seqs
    fetch_maxids_if_needed(context=MaxIdFetchContext.CONTEXT_AUTOUPDATE)
    for dt, maxid_str in Config.fetched_maxids.items():
        maxid = int(maxid_str)
        for cat in autoupdate_seqs:
            uidseq: IntSequence | None = autoupdate_seqs[cat][dt]
            if uidseq:
                update_str_base = f'{cat}:{dt} id sequence extended from {uidseq.ints!s} to '
                if len(uidseq) == 1 and uidseq[0] < 0:
                    if maxid + uidseq.ints[0] <= 0:
                        trace(f'{cat}:{dt} id sequence extension <= 0 detected! Clamping to \'1\'!')
                        uidseq.ints[0] = -1 * (maxid - 1)
                    delta = uidseq.ints[0]
                    uidseq.ints.clear()
                    uidseq.ints.extend((maxid + delta, maxid))
                else:
                    uidseq.ints.append(maxid)
                trace(f'{update_str_base}{uidseq.ints!s}')
    for cat in queries.sequences_ids:
        for dt in queries.sequences_ids[cat]:
            if queries.sequences_ids[cat][dt] is not None and len(queries.sequences_ids[cat][dt]) < MIN_IDS_SEQ_LENGTH:
                unsolved_idseqs.append(f'{cat}:{dt}')
                trace(f'{cat}:{dt} sequence is not fixed! \'{queries.sequences_ids[cat][dt]!s}\'')
    assert len(unsolved_idseqs) == 0


def prepare_queries() -> None:
    queries = Config.parser.queries
    trace('Analyzing queries file strings...')
    Config.parser.parse_queries_file()
    trace('Sequences parsed successfully\n')
    fetch_maxids_if_needed(context=MaxIdFetchContext.CONTEXT_PREFETCH)
    if queries.autoupdate_seqs:
        trace('[Autoupdate] validating runners...\n')
        validate_runners(queries)
        run_autoupdates()
    trace('Validating sequences...\n')
    validate_sequences(queries)
    validate_runners(queries)
    trace('Sequences validated. Finalizing...\n')
    if Config.debug:
        trace('[DEBUG] Unoptimized:')
        report_unoptimized(queries)
        trace('\n\nFinals:')
    queries_final = form_queries(queries)
    report_queries(queries_final)
    register_queries(queries_final)


def update_next_ids() -> None:
    if Config.update is False:
        trace('\nNext ids update SKIPPED due to no --update flag!')
        return

    if Config.test:
        return

    # save backup and write a new one
    trace('\nNext ids update initiated...')

    queries = Config.parser.queries
    queries_file_name = Config.script_path[Config.script_path.rfind(SLASH) + 1:]

    filename_bak = f'{queries_file_name}_bak_{datetime_str_nfull()}.list'
    trace(f'File: \'{queries_file_name}\', backup file: \'{filename_bak}\'')
    try:
        fetch_maxids_if_needed(context=MaxIdFetchContext.CONTEXT_UPDATE_NEXT)
        if Config.fetched_maxids:
            trace(f'\nSaving backup to \'{filename_bak}\'...')
            bak_fullpath = f'{Config.dest_bak_base}{filename_bak}'
            with open(bak_fullpath, 'wt', encoding=UTF8, buffering=1) as outfile_bak:
                outfile_bak.writelines(queries.queries_file_lines)
                trace('Saving done')

            trace(f'\nSetting read-only permissions for \'{filename_bak}\'...')
            perm = 0
            try:
                os.chmod(bak_fullpath, 0o100444)  # S_IFREG | S_IRUSR | S_IRGRP | S_IROTH
                perm = os.stat(bak_fullpath).st_mode
                assert (perm & 0o777) == 0o444
                trace('Permissions successfully updated')
            except AssertionError:
                trace(f'Warning: permissions mismatch \'{perm:o}\' != \'444\', manual fix required')
            except Exception:
                trace('Warning: permissions not updated, manual fix required')

            trace(f'\nWriting updated queries to \'{queries_file_name}\'...')
            maxids: dict[str, int] = {dt: int(Config.fetched_maxids[dt]) for dt in Config.fetched_maxids}
            for dt in Config.update_offsets:
                uoffset = Config.update_offsets[dt]
                if dt in maxids:
                    maxids[dt] += uoffset
                    trace(f'Applying {dt.upper()} update offset {uoffset:d}: {maxids[dt] - uoffset:d} -> {maxids[dt]:d}')
                else:
                    trace(f'Warning: {dt.upper()} autoupdate offset ({uoffset:d}) was provided but its max id is not being updated')
            cat: str
            for cat in queries.sequences_ids:
                dtseq: tuple[str, IntSequence | None]
                for i, dtseq in enumerate(queries.sequences_ids[cat].items()):
                    dt, seq = dtseq
                    line_n = (seq.line_num - 1) if seq and dt in maxids else None
                    trace(f'{"W" if line_n else "Not w"}riting \'{cat}:{dt}\' ids at idx {i:d}, line {line_n + 1 if line_n else -1:d}...')
                    if line_n:
                        ids_at_line = queries.queries_file_lines[line_n].strip().split(' ')
                        queries.queries_file_lines[line_n] = ' '.join((ids_at_line[0], *ids_at_line[2:], f'{maxids[dt]:d}\n'))
                trace(f'Writing \'{cat}\' ids done')
            with open(Config.script_path, 'wt', encoding=UTF8, buffering=1) as outfile:
                outfile.writelines(queries.queries_file_lines)
            trace('Writing done\n\nNext ids update successfully completed')
        else:
            trace('No id sequences were used, next ids update cancelled')
    except Exception:
        trace(f'\nError: failed to update next ids, you\'ll have to do it manually!! (backup has to be {filename_bak})\n')
        raise

#
#
#########################################
