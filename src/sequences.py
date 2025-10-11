# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from collections.abc import Sequence
from re import compile as re_compile
from subprocess import check_output

from defs import (
    DownloadCollection, IntPair, Config, IntSequence, DOWNLOADERS, RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, RANGE_TEMPLATE_PAGE_IDS,
    RUXX_DOWNLOADERS, APP_NAMES, PATH_APPEND_DOWNLOAD_IDS, PATH_APPEND_DOWNLOAD_PAGES, MIN_PYTHON_VERSION, MIN_PYTHON_VERSION_STR,
    unused_argument,
)
from logger import trace
from strings import NEWLINE, path_args

__all__ = ('validate_runners', 'validate_sequences', 'form_queries', 'report_queries', 'report_unoptimized')


def validate_runners(
    sequences_paths: DownloadCollection[str],
    sequences_paths_reqs: dict[str, str | None],
    sequences_paths_update: dict[str, str | None]
) -> None:
    try:
        trace('Looking for python executable...')
        re_py_ver = re_compile(r'^[Pp]ython (\d)\.(\d{1,2})\.(\d+)$')
        out_py = check_output((Config.python, '-V'))
        out_py_str = out_py.decode().strip()
        match_py_ver = re_py_ver.fullmatch(out_py_str)
        assert match_py_ver
        fetched_py_ver = (int(match_py_ver.group(1)), int(match_py_ver.group(2)))
        assert fetched_py_ver >= MIN_PYTHON_VERSION, f'Minimum python version required is {MIN_PYTHON_VERSION_STR}!'
        trace(f'Found python {".".join(match_py_ver.groups())}')
    except Exception:
        trace('Error: invalid python executable!')
        raise IOError
    if Config.test is True:
        return
    checked_reqs = set[str]()
    if Config.install:
        for dtr, rpath in sequences_paths_reqs.items():
            if not rpath or dtr not in Config.downloaders:
                continue
            if rpath in checked_reqs:
                trace(f'{dtr} requirements path is already checked!')
                continue
            checked_reqs.add(rpath)
            try:
                trace(f'Installing {dtr} requirements...')
                trace(check_output((Config.python, '-m', 'pip', 'install', '-r', rpath), universal_newlines=True).strip())
                trace('Done')
            except Exception:
                trace(f'Error: invalid {dtr} requirements path found: \'{rpath}\'!')
                raise IOError
    checked_paths: set[str] = set()
    if not Config.no_download:
        for cat in sequences_paths:
            for dtd in sequences_paths[cat]:
                dpath: str | None = sequences_paths[cat][dtd]
                if not dpath or dtd not in Config.downloaders:
                    continue
                dtype = ('pages' if dpath.endswith(PATH_APPEND_DOWNLOAD_PAGES[dtd]) else
                         'ids' if dpath.endswith(PATH_APPEND_DOWNLOAD_IDS[dtd]) else 'unknown')
                if dpath in checked_paths:
                    trace(f'{dtd} {dtype} downloader path is already checked!')
                    continue
                checked_paths.add(dpath)
                try:
                    trace(f'Looking for {dtd} {dtype} downloader...')
                    out_d = check_output((Config.python, dpath, '--version'))
                    out_d_str = out_d.decode().strip()
                    out_d_str = out_d_str[out_d_str.rfind('\n') + 1:]
                    assert out_d_str.startswith(APP_NAMES[dtd]), f'Unexpected output for {dtd}: {out_d_str[:min(len(out_d_str), 20)]}!'
                    trace(f'Found \'{dpath}\'')
                except Exception:
                    trace(f'Error: invalid {dtd} {dtype} downloader found at: \'{dpath}\' ({cat})!')
                    raise IOError
    if Config.update:
        for dtu, upath in sequences_paths_update.items():
            if not upath or dtu not in Config.downloaders:
                continue
            if upath in checked_paths:
                trace(f'{dtu} updater path is already checked!')
                continue
            checked_paths.add(upath)
            try:
                trace(f'Looking for {dtu} updater...')
                out_u = check_output((Config.python, upath, '--version'))
                out_u_str = out_u.decode().strip()
                out_u_str = out_u_str[out_u_str.rfind('\n') + 1:]
                assert out_u_str.startswith(APP_NAMES[dtu]), f'Unexpected output for {dtu}: {out_u_str[:min(len(out_u_str), 20)]}!'
                trace(f'Found \'{upath}\'')
            except Exception:
                trace(f'Error: invalid {dtu} updater found at: \'{upath}\'!')
                raise IOError


def validate_sequences(
    sequences_ids: DownloadCollection[IntSequence], sequences_pages: DownloadCollection[IntSequence],
    sequences_paths: DownloadCollection[str], sequences_tags: DownloadCollection[Sequence[list[str]]],
    sequences_subfolders: DownloadCollection[Sequence[str]]
) -> None:
    unused_argument(sequences_pages)
    if not Config.python:
        trace('Error: python executable was not declared!')
        raise IOError
    cat: str
    if Config.categories:
        for cat in sequences_subfolders:
            if cat not in Config.categories:
                trace(f'Warning: category \'{cat}\' is not in enabled categories list! Will be skipped!')
                if cat not in Config.disabled_downloaders:
                    Config.disabled_downloaders[cat] = set()
                [Config.disabled_downloaders[cat].add(dt) for dt in DOWNLOADERS]
    for dt in DOWNLOADERS:
        for cat in sequences_ids:
            intseq: IntSequence | None = sequences_ids[cat][dt]
            ivlist = list(intseq.ints if intseq else [])
            for iv in range(1, len(ivlist)):
                if ivlist[iv - 1] >= ivlist[iv]:
                    if ivlist[iv - 1] > ivlist[iv] or iv > 1:
                        trace(f'Error: {cat}:{dt} ids sequence is corrupted at idx {iv - 1:d}, {ivlist[iv - 1]:d} >= {ivlist[iv]:d}!')
                        raise IOError
                    else:
                        trace(f'{cat}:{dt} ids sequence forms zero-length range {ivlist[iv - 1]:d}-{ivlist[iv] - 1:d}! Will be skipped!')
                        if cat not in Config.disabled_downloaders:
                            Config.disabled_downloaders[cat] = set()
                        Config.disabled_downloaders[cat].add(dt)
        for cat in sequences_paths:
            if (not not sequences_paths[cat][dt]) != (not not (sequences_ids[cat][dt] or sequences_tags[cat][dt])):
                trace(f'Error: sequence list existance for {cat}:{dt} paths/ids mismatch!')
                raise IOError
        for cat in sequences_tags:
            len1, len2 = len(sequences_tags[cat][dt]), len(sequences_subfolders[cat][dt])
            if len1 != len2:
                trace(f'Error: sequence list for {cat} tags/subs mismatch for {dt}: {len1:d} vs {len2:d}!')
                raise IOError


def _get_base_qs(
    sequences_ids: DownloadCollection[IntSequence],
    sequences_pages: DownloadCollection[IntSequence],
    sequences_paths: DownloadCollection[str]
) -> DownloadCollection[str]:
    def has_ids(cat: str, cdt: str) -> bool:
        return not not (sequences_ids[cat] and sequences_ids[cat][cdt])

    def has_pages(cat: str, cdt: str) -> bool:
        return not not (sequences_pages[cat] and sequences_pages[cat][cdt])

    def pure_ids(cat: str, cdt: str) -> bool:
        return has_ids(cat, cdt) and not has_pages(cat, cdt)

    def page_ids(cat: str, cdt: str) -> bool:
        return has_ids(cat, cdt) and has_pages(cat, cdt)

    base_qs: DownloadCollection[str] = DownloadCollection()
    ri, rp, rpi = RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, RANGE_TEMPLATE_PAGE_IDS
    irngs: dict[str, dict[str, IntPair]]
    prngs: dict[str, dict[str, IntPair]]
    irngs, prngs = ({
        k: {dt: IntPair(*ipseqs[k][dt][:2]) for dt in DOWNLOADERS if ipseqs[k][dt]} for k in ipseqs
    } for ipseqs in (sequences_ids, sequences_pages))
    [base_qs.update({
        k: {
            dt: (f'{Config.python} "{sequences_paths[k][dt]}" '
                 f'{(ri[dt].first % irngs[k][dt].first) if pure_ids(k, dt) else (rp[dt].first % prngs[k][dt].first)}'
                 f'{(ri[dt].second % (irngs[k][dt].second - 1)) if pure_ids(k, dt) else (rp[dt].second % prngs[k][dt].second)}'
                 f'{f" {rpi[dt].first % irngs[k][dt].first}" if page_ids(k, dt) and irngs[k][dt].first else ""}'
                 f'{f" {rpi[dt].second % (irngs[k][dt].second - 1)}" if page_ids(k, dt) and irngs[k][dt].second else ""}')
            for dt in DOWNLOADERS if (dt in irngs[k] or dt in prngs[k])
        }
    }) for k in sequences_paths]
    return base_qs


def form_queries(
    sequences_ids: DownloadCollection[IntSequence], sequences_pages: DownloadCollection[IntSequence],
    sequences_paths: DownloadCollection[str], sequences_tags: DownloadCollection[Sequence[list[str]]],
    sequences_subfolders: DownloadCollection[Sequence[str]], sequences_common: DownloadCollection[Sequence[str]]
) -> DownloadCollection[list[str]]:
    stags, ssubs, scomms = sequences_tags, sequences_subfolders, sequences_common
    base_qs = _get_base_qs(sequences_ids, sequences_pages, sequences_paths)
    queries_final: DownloadCollection[list[str]] = DownloadCollection()
    [queries_final.update({
        k: {
            dt: ([f'{base_qs[k][dt]} {path_args(Config.dest_base, k, ssubs[k][dt][i], Config.datesub)} '
                  f'{" ".join(scomms[k][dt])} {" ".join(staglist)}'
                  for i, staglist in enumerate(stags[k][dt]) if staglist])
            if dt in RUXX_DOWNLOADERS or any(any(sarg.startswith('-search') for sarg in slist) for slist in stags[k][dt]) else
                ([f'{base_qs[k][dt]} {path_args(Config.dest_base, k, "", Config.datesub)} '
                  f'{" ".join(scomms[k][dt])} '
                  f'-script "'
                  f'{"; ".join(" ".join([f"{ssubs[k][dt][i]}:"] + staglist) for i, staglist in enumerate(stags[k][dt]))}'
                  f'"'] if stags[k][dt] else [])
            for dt in DOWNLOADERS
        }
    }) for k in sequences_paths]
    return queries_final


def report_unoptimized(
    sequences_ids: DownloadCollection[IntSequence], sequences_pages: DownloadCollection[IntSequence],
    sequences_paths: DownloadCollection[str], sequences_tags: DownloadCollection[Sequence[list[str]]],
    sequences_subfolders: DownloadCollection[Sequence[str]], sequences_common: DownloadCollection[Sequence[str]]
) -> None:
    stags, ssubs, scomms = sequences_tags, sequences_subfolders, sequences_common
    base_qs = _get_base_qs(sequences_ids, sequences_pages, sequences_paths)
    queries: DownloadCollection[list[str]] = DownloadCollection()
    [queries.update({
        k: {
            dt: ([f'{base_qs[k][dt]} {path_args(Config.dest_base, k, ssubs[k][dt][i], Config.datesub)} '
                  f'{" ".join(scomms[k][dt])} {" ".join(staglist)}'
                  for i, staglist in enumerate(stags[k][dt]) if staglist])
            for dt in DOWNLOADERS
        }
    }) for k in sequences_paths]
    report_queries(queries)


def report_queries(queries: DownloadCollection[list[str]]) -> None:
    for cat in queries:
        trace(f'\nQueries \'{cat}\':\n{NEWLINE.join(NEWLINE.join(queries[cat][dt]) for dt in queries[cat] if queries[cat][dt])}', False)

#
#
#########################################
