# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile
from subprocess import check_output
from typing import Dict, List, Sequence, Optional, Any

from defs import (
    DownloadCollection, IntPair, Config, IntSequence, DOWNLOADERS, RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, RUXX_DOWNLOADERS,
    STOP_ID_TEMPLATE, BEGIN_ID_TEMPLATE, APP_NAMES
)
from logger import trace
from strings import NEWLINE, normalize_ruxx_tag, path_args

__all__ = ('validate_sequences', 'form_queries', 'report_finals')


def unused_argument(arg: Any) -> None:
    bool(arg)


def validate_sequences(
    sequences_ids: List[DownloadCollection[IntSequence]], sequences_pages: List[DownloadCollection[IntSequence]],
    sequences_paths: List[DownloadCollection[str]], sequences_tags: List[DownloadCollection[Sequence[List[str]]]],
    sequences_subfolders: List[DownloadCollection[Sequence[str]]], sequences_paths_update: Dict[str, Optional[str]]
) -> None:
    unused_argument(sequences_pages)
    unused_argument(sequences_subfolders)
    if not Config.python:
        trace('Error: python executable was not declared!')
        raise IOError
    for dt in DOWNLOADERS:
        for sids in sequences_ids:
            ivlist = list(sids[dt].ints if sids[dt] else [])
            for iv in range(1, len(ivlist)):
                if ivlist[iv - 1] >= ivlist[iv]:
                    trace(f'Error: {sids.name}:{dt} ids sequence is corrupted at idx {iv - 1:d}, {ivlist[iv - 1]:d} >= {ivlist[iv]:d}!')
                    raise IOError
        for spaths in sequences_paths:
            if (not not spaths[dt]) != (not not (spaths[dt] or spaths[dt])):
                trace(f'Error: sequence list existance for {spaths.name} tags/ids mismatch for {dt}!')
                raise IOError
        for stags in sequences_tags:
            len1, len2 = len(stags[dt]), len(stags[dt])
            if len1 != len2:
                trace(f'Error: sequence list for {stags.name} tags/subs mismatch for {dt}: {len1:d} vs {len2:d}!')
                raise IOError
    try:
        trace('Looking for python executable...')
        re_py_ver = re_compile(r'^[Pp]ython (\d)\.(\d{1,2})\.(\d+)$')
        out_py = check_output((Config.python, '-V'))
        out_py_str = out_py.decode().strip()
        match_py_ver = re_py_ver.fullmatch(out_py_str)
        assert match_py_ver
        assert (int(match_py_ver.group(1)), int(match_py_ver.group(2))) >= (3, 7), 'Minimum python version required is 3.7!'
        trace(f'Found python {".".join(match_py_ver.groups())}')
    except Exception:
        trace('Error: invalid python executable!')
        raise IOError
    if Config.test is True:
        return
    checked_paths = set()
    if not Config.no_download:
        for spaths in sequences_paths:
            for dtd, dpath in (spaths.dls.items()):
                if not dpath or dtd not in Config.downloaders:
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
                except Exception:
                    trace(f'Error: invalid {dtd} downloader found at: \'{dpath}\' ({spaths.name})!')
                    raise IOError
    if Config.update:
        for dtu, upath in sequences_paths_update.items():  # type: str, Optional[str]
            if not upath:
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
            except Exception:
                trace(f'Error: invalid {dtu} updater found at: \'{upath}\'!')
                raise IOError


def _get_base_qs(
    sequences_ids: List[DownloadCollection[IntSequence]], sequences_pages: List[DownloadCollection[IntSequence]],
    sequences_paths: List[DownloadCollection[str]]
) -> Dict[str, Dict[str, str]]:
    def any_ids(cdt: str) -> bool:
        return not not any(idseq[cdt] for idseq in sequences_ids)

    def pure_ids(cdt: str) -> bool:
        return not not (any_ids(cdt) and not any(pseq[cdt] for pseq in sequences_pages))

    def page_ids(cdt: str) -> bool:
        return pure_ids(cdt) is False and any_ids(cdt) is True

    ri, rp, rs, rb = RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, STOP_ID_TEMPLATE, BEGIN_ID_TEMPLATE
    irngs, prngs = ({
        ipseq.name: {dt: IntPair(ipseq.dls[dt][:2]) for dt in DOWNLOADERS if ipseq[dt]} for ipseq in ipseqs
    } for ipseqs in (sequences_ids, sequences_pages))  # type: Dict[str, Dict[str, IntPair]]
    base_qs = {
        pseq.name: {
            dt: (f'{Config.python} "{pseq.dls[dt]}" '
                 f'{(ri[dt].first % irngs[pseq.name][dt].first) if pure_ids(dt) else (rp[dt].first % prngs[pseq.name][dt].first)} '
                 f'{(ri[dt].second % (irngs[pseq.name][dt].second - 1)) if pure_ids(dt) else (rp[dt].second % prngs[pseq.name][dt].second)}'
                 f'{f" {rs % irngs[pseq.name][dt].first}" if irngs[pseq.name][dt].first and page_ids(dt) else ""}'
                 f'{f" {rb % irngs[pseq.name][dt].second}" if irngs[pseq.name][dt].second and page_ids(dt) else ""}')
            for dt in DOWNLOADERS if (dt in irngs[pseq.name] or dt in prngs[pseq.name])
        } for pseq in sequences_paths
    }  # type: Dict[str, Dict[str, str]]
    return base_qs


def form_queries(
    sequences_ids: List[DownloadCollection[IntSequence]], sequences_pages: List[DownloadCollection[IntSequence]],
    sequences_paths: List[DownloadCollection[str]], sequences_tags: List[DownloadCollection[Sequence[List[str]]]],
    sequences_subfolders: List[DownloadCollection[Sequence[str]]], sequences_common: List[DownloadCollection[Sequence[str]]]
) -> Dict[str, Dict[str, List[str]]]:
    stags, ssubs, scomms = sequences_tags, sequences_subfolders, sequences_common
    base_qs = _get_base_qs(sequences_ids, sequences_pages, sequences_paths)
    queries_final = {
        cat: {
            dt: ([f'{base_qs[cat][dt]} {path_args(Config.dest_base, cat, ssubs[idx][dt][i], not Config.no_date_path)} '
                  f'{" ".join(normalize_ruxx_tag(tag) if dt in RUXX_DOWNLOADERS else tag for tag in scomms[idx][dt])} '
                  f'{" ".join(normalize_ruxx_tag(tag) if dt in RUXX_DOWNLOADERS else tag for tag in staglist)}'
                  for i, staglist in enumerate(stags[idx][dt]) if staglist]
                 ) if dt in RUXX_DOWNLOADERS or any(any(sarg.startswith('-search') for sarg in slist) for slist in stags[idx][dt]) else
                ([f'{base_qs[cat][dt]} {path_args(Config.dest_base, cat, "", not Config.no_date_path)} '
                  f'{" ".join(scomms[idx][dt])} '
                  f'-script "'
                  f'{"; ".join(" ".join([f"{ssubs[idx][dt][i]}:"] + staglist) for i, staglist in enumerate(stags[idx][dt]))}'
                  f'"'] if stags[idx][dt] else []
                 )
            for dt in DOWNLOADERS
        } for idx, cat in ((idx, dc.name) for idx, dc in enumerate(sequences_paths))
    }  # type: Dict[str, Dict[str, List[str]]]
    return queries_final


def report_finals(queries_final: Dict[str, Dict[str, List[str]]], cat_names: List[str]) -> None:
    for ty in cat_names:
        trace(f'\nQueries {ty}:\n{NEWLINE.join(NEWLINE.join(finals) for finals in queries_final[ty].values() if finals)}', False)

#
#
#########################################
