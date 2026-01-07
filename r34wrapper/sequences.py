# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import re
from subprocess import check_output

from .config import Config
from .containers import DownloadCollection, Queries
from .defs import (
    APP_NAMES,
    DOWNLOADERS,
    MIN_PYTHON_VERSION,
    MIN_PYTHON_VERSION_STR,
    PAGE_DOWNLOADERS,
    RANGE_TEMPLATE_IDS,
    RANGE_TEMPLATE_PAGE_IDS,
    RANGE_TEMPLATE_PAGES,
    RUXX_DOWNLOADERS,
    IntPair,
    IntSequence,
)
from .logger import trace
from .strings import NEWLINE, path_args

__all__ = ('form_queries', 'report_queries', 'report_unoptimized', 'validate_runners', 'validate_sequences')

_validated_runners = set[str]()


def validate_runners(queries: Queries) -> None:
    if 'all' in _validated_runners:
        return

    checked_reqs = set[str]()
    checked_paths = set[str]()

    runner_type_python = 'python'
    if runner_type_python not in _validated_runners:
        trace('Looking for python executable...')
        re_py_ver = re.compile(r'^[Pp]ython (\d)\.(\d{1,2})\.(\d+)$')
        out_py = check_output((Config.python, '-V'))
        out_py_str = out_py.decode().strip()
        match_py_ver = re_py_ver.fullmatch(out_py_str)
        if not match_py_ver:
            raise OSError(f'Error: invalid python executable \'{Config.python}\'!')
        fetched_py_ver = int(match_py_ver.group(1)), int(match_py_ver.group(2))
        if fetched_py_ver < MIN_PYTHON_VERSION:
            raise OSError(f'Minimum python version required is {MIN_PYTHON_VERSION_STR}!')
        _validated_runners.add(runner_type_python)
        trace(f'Found python {".".join(match_py_ver.groups())}')
    if Config.test is True:
        return
    if Config.install:
        for dtr, rpath in queries.sequences_paths_reqs.items():
            runner_type_install = f'{dtr}_install'
            if not rpath or runner_type_install in _validated_runners or dtr not in Config.downloaders:
                continue
            if rpath in checked_reqs:
                trace(f'{dtr} requirements path is already checked!')
                continue
            checked_reqs.add(rpath)
            try:
                trace(f'Installing {dtr} requirements...')
                trace(check_output((Config.python, '-m', 'pip', 'install', '-r', rpath), universal_newlines=True).strip())
                _validated_runners.add(runner_type_install)
                trace('Done')
            except Exception:
                trace(f'Error: invalid {dtr} requirements path found: \'{rpath}\'!')
                raise OSError
    if not Config.no_download:
        for cat in queries.sequences_paths:
            for dtd in queries.sequences_paths[cat]:
                dpath = queries.sequences_paths[cat][dtd]
                if not dpath or dtd not in Config.downloaders:
                    continue
                runner_type_download = f'{dtd}_download'
                if runner_type_download in _validated_runners:
                    continue
                if dpath in checked_paths:
                    trace(f'{dtd} downloader path is already checked!')
                    continue
                checked_paths.add(dpath)
                try:
                    trace(f'Looking for {dtd} downloader...')
                    out_d = check_output((Config.python, dpath, '--version'))
                    out_d_str = out_d.decode().strip()
                    out_d_str = out_d_str[out_d_str.rfind('\n') + 1:]
                    assert out_d_str.startswith(APP_NAMES[dtd]), f'Unexpected output for {dtd}: {out_d_str[:min(len(out_d_str), 20)]}!'
                    _validated_runners.add(runner_type_download)
                    trace(f'Found \'{dpath}\'')
                except Exception:
                    trace(f'Error: invalid {dtd} downloader found at: \'{dpath}\' ({cat})!')
                    raise OSError
    if Config.update:
        for dtu, upath in queries.sequences_paths_update.items():
            if not upath or dtu not in Config.downloaders:
                continue
            runner_type_update = f'{dtu}_update'
            if runner_type_update in _validated_runners:
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
                _validated_runners.add(runner_type_update)
                trace(f'Found \'{upath}\'')
            except Exception:
                trace(f'Error: invalid {dtu} updater found at: \'{upath}\'!')
                raise OSError
    _validated_runners.add('all')


def validate_sequences(queries: Queries) -> None:
    if not Config.python:
        trace('Error: python executable was not declared!')
        raise OSError
    cat: str
    if Config.categories:
        for cat in queries.sequences_subfolders:
            if cat not in Config.categories:
                trace(f'Warning: category \'{cat}\' is not in enabled categories list! Will be skipped!')
                Config.disabled_downloaders[cat] = set(DOWNLOADERS)
    for dt in DOWNLOADERS:
        for cat in queries.sequences_ids:
            intseq: IntSequence | None = queries.sequences_ids[cat][dt]
            ivlist = list(intseq.ints if intseq else [])
            for iv in range(1, len(ivlist)):
                if ivlist[iv - 1] >= ivlist[iv]:
                    if ivlist[iv - 1] > ivlist[iv] or iv > 1:
                        trace(f'Error: {cat}:{dt} ids sequence is corrupted at idx {iv - 1:d}, {ivlist[iv - 1]:d} >= {ivlist[iv]:d}!')
                        raise OSError
                    else:
                        trace(f'{cat}:{dt} ids sequence forms zero-length range {ivlist[iv - 1]:d}-{ivlist[iv] - 1:d}! Will be skipped!')
                        if cat not in Config.disabled_downloaders:
                            Config.disabled_downloaders[cat] = set()
                        Config.disabled_downloaders[cat].add(dt)
        for cat in queries.sequences_paths:
            if bool(queries.sequences_paths[cat][dt]) != (bool(queries.sequences_ids[cat][dt] or queries.sequences_tags[cat][dt])):
                trace(f'Error: sequence list existance for {cat}:{dt} paths/ids mismatch!')
                raise OSError
        for cat in queries.sequences_tags:
            len1, len2 = len(queries.sequences_tags[cat][dt]), len(queries.sequences_subfolders[cat][dt])
            if len1 != len2:
                trace(f'Error: sequence list for {cat} tags/subs mismatch for {dt}: {len1:d} vs {len2:d}!')
                raise OSError


def _get_base_qs(queries: Queries) -> DownloadCollection[str]:
    def has_ids(cat: str, cdt: str) -> bool:
        return bool(queries.sequences_ids[cat] and queries.sequences_ids[cat][cdt])

    def has_pages(cat: str, cdt: str) -> bool:
        return bool(queries.sequences_pages[cat] and queries.sequences_pages[cat][cdt])

    def pure_ids(cat: str, cdt: str) -> bool:
        return has_ids(cat, cdt) and not has_pages(cat, cdt)

    def page_ids(cat: str, cdt: str) -> bool:
        return has_ids(cat, cdt) and has_pages(cat, cdt)

    ri, rp, rpi = RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, RANGE_TEMPLATE_PAGE_IDS
    irngs: dict[str, dict[str, IntPair]]
    prngs: dict[str, dict[str, IntPair]]
    irngs, prngs = ({
        k: {dt: IntPair(*ipseqs[k][dt][:2]) for dt in DOWNLOADERS if ipseqs[k][dt]} for k in ipseqs
    } for ipseqs in (queries.sequences_ids, queries.sequences_pages))
    piargs: dict[str, dict[str, str]]
    piargs = ({
        k: {dt: 'pages ' if has_pages(k, dt) else 'ids ' if dt in PAGE_DOWNLOADERS else '' for dt in DOWNLOADERS}
        for k in queries.sequences_paths
    })
    base_qs: DownloadCollection[str] = DownloadCollection()
    [base_qs.update({
        k: {
            dt: (f'{Config.python} "{queries.sequences_paths[k][dt]}" {piargs[k][dt]}'
                 f'{(ri[dt].first % irngs[k][dt].first) if pure_ids(k, dt) else (rp[dt].first % prngs[k][dt].first)}'
                 f'{(ri[dt].second % (irngs[k][dt].second - 1)) if pure_ids(k, dt) else (rp[dt].second % prngs[k][dt].second)}'
                 f'{f" {rpi[dt].first % irngs[k][dt].first}" if page_ids(k, dt) and irngs[k][dt].first else ""}'
                 f'{f" {rpi[dt].second % (irngs[k][dt].second - 1)}" if page_ids(k, dt) and irngs[k][dt].second else ""}')
            for dt in DOWNLOADERS if (dt in irngs[k] or dt in prngs[k])
        },
    }) for k in queries.sequences_paths]
    return base_qs


def form_queries(qs: Queries) -> DownloadCollection[list[str]]:
    stags, ssubs, scomms, spaths = qs.sequences_tags, qs.sequences_subfolders, qs.sequences_common, qs.sequences_paths
    base_qs = _get_base_qs(qs)
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
                  f'{"; ".join(" ".join([f"{ssubs[k][dt][i]}:", *staglist]) for i, staglist in enumerate(stags[k][dt]))}'
                  f'"'] if stags[k][dt] else [])
            for dt in DOWNLOADERS
        },
    }) for k in spaths]
    return queries_final


def report_unoptimized(qs: Queries) -> None:
    stags, ssubs, scomms, spaths = qs.sequences_tags, qs.sequences_subfolders, qs.sequences_common, qs.sequences_paths
    base_qs = _get_base_qs(qs)
    queries: DownloadCollection[list[str]] = DownloadCollection()
    [queries.update({
        k: {
            dt: ([f'{base_qs[k][dt]} {path_args(Config.dest_base, k, ssubs[k][dt][i], Config.datesub)} '
                  f'{" ".join(scomms[k][dt])} {" ".join(staglist)}'
                  for i, staglist in enumerate(stags[k][dt]) if staglist])
            for dt in DOWNLOADERS
        },
    }) for k in spaths]
    report_queries(queries)


def report_queries(queries: DownloadCollection[list[str]]) -> None:
    for cat in queries:
        trace(f'\nQueries \'{cat}\':\n{NEWLINE.join(NEWLINE.join(queries[cat][dt]) for dt in queries[cat] if queries[cat][dt])}', False)

#
#
#########################################
