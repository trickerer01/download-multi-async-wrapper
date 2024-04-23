# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile
from subprocess import check_output
from typing import Dict, List, Tuple, Optional, Mapping, Sequence, TypeVar

from defs import (
    IntPair, Config, IntSequence, DOWNLOADERS, RANGE_TEMPLATE_IDS, RANGE_TEMPLATE_PAGES, RUXX_DOWNLOADERS,
    STOP_ID_TEMPLATE, BEGIN_ID_TEMPLATE, APP_NAMES)
from logger import trace
from strings import NEWLINE, normalize_ruxx_tag, path_args

__all__ = ('validate_sequences', 'queries_from_sequences', 'report_finals')

IntSequenceMap = TypeVar('IntSequenceMap', bound=Mapping[str, Optional[IntSequence]])
StringMap = TypeVar('StringMap', bound=Mapping[str, Optional[str]])
StringListMap = TypeVar('StringListMap', bound=Mapping[str, Sequence[str]])
StringListListMap = TypeVar('StringListListMap', bound=Mapping[str, Sequence[List[str]]])


def validate_sequences(
    sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
    sequences_pages_vid: IntSequenceMap, sequences_pages_img: IntSequenceMap,
    sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
    sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
    sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
    sequences_paths_update: StringMap
) -> None:
    if not Config.python:
        trace('Error: python executable was not declared!')
        raise IOError
    for dt in DOWNLOADERS:
        ivlist = list(sequences_ids_vid[dt].ints if sequences_ids_vid[dt] else [])  # type: List[int]
        for iv in range(1, len(ivlist)):
            if ivlist[iv - 1] >= ivlist[iv]:
                trace(f'Error: {dt} vid ids sequence is corrupted at idx {iv - 1:d}, {ivlist[iv - 1]:d} >= {ivlist[iv]:d}!')
                raise IOError
        iilist = list(sequences_ids_img[dt].ints if sequences_ids_img[dt] else [])
        for ii in range(len(iilist)):
            if ii > 0 and iilist[ii - 1] >= iilist[ii]:
                trace(f'Error: {dt} img ids sequence is corrupted at idx {ii - 1:d}, {iilist[ii - 1]:d} >= {iilist[ii]:d}!')
                raise IOError
        if (not not sequences_paths_vid[dt]) != (not not (sequences_ids_vid[dt] or sequences_pages_vid[dt])):
            trace(f'Error: sequence list existance for vid tags/ids mismatch for {dt}!')
            raise IOError
        if (not not sequences_paths_img[dt]) != (not not (sequences_ids_img[dt] or sequences_pages_img[dt])):
            trace(f'Error: sequence list existance for img tags/ids mismatch for {dt}!')
            raise IOError
        len1, len2 = len(sequences_tags_vid[dt]), len(sequences_subfolders_vid[dt])
        if len1 != len2:
            trace(f'Error: sequence list for vid tags/subs mismatch for {dt}: {len1:d} vs {len2:d}!')
            raise IOError
        len1, len2 = len(sequences_tags_img[dt]), len(sequences_subfolders_img[dt])
        if len1 != len2:
            trace(f'Error: sequence list for img tags/subs mismatch for {dt}: {len1:d} vs {len2:d}!')
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
        for dtd, dpath in (list(sequences_paths_vid.items()) + list(sequences_paths_img.items())):  # type: str, Optional[str]
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
                trace(f'Error: invalid {dtd} downloader found at: \'{dpath}\'!')
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
    sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
    sequences_pages_vid: IntSequenceMap, sequences_pages_img: IntSequenceMap,
    sequences_paths_vid: StringMap, sequences_paths_img: StringMap
) -> Tuple[Dict[str, str], Dict[str, str]]:
    def any_ids(cdt: str) -> bool:
        return not not (sequences_ids_vid[cdt] or sequences_ids_img[cdt])

    def pure_ids(cdt: str) -> bool:
        return not not (any_ids(cdt) and not (sequences_pages_vid[cdt] or sequences_pages_img[cdt]))

    def page_ids(cdt: str) -> bool:
        return pure_ids(cdt) is False and any_ids(cdt) is True

    ri = RANGE_TEMPLATE_IDS
    rp = RANGE_TEMPLATE_PAGES
    rs = STOP_ID_TEMPLATE
    rb = BEGIN_ID_TEMPLATE
    virange, iirange = (
        {dt: IntPair(sids[dt][:2]) for dt in DOWNLOADERS if sids[dt]} for sids in (sequences_ids_vid, sequences_ids_img)
    )  # type: Dict[str, IntPair]
    vprange, iprange = (
        {dt: IntPair(spages[dt][:2]) for dt in DOWNLOADERS if spages[dt]} for spages in (sequences_pages_vid, sequences_pages_img)
    )  # type: Dict[str, IntPair]
    base_q_v, base_q_i = ({
        dt: (f'{Config.python} "{spath[dt]}" '
             f'{(ri[dt].first % sirange[dt].first) if pure_ids(dt) else (rp[dt].first % sprange[dt].first)} '
             f'{(ri[dt].second % (sirange[dt].second - 1)) if pure_ids(dt) else (rp[dt].second % sprange[dt].second)}'
             f'{f" {rs % sirange[dt].first}" if sirange[dt].first and page_ids(dt) else ""}'
             f'{f" {rb % sirange[dt].second}" if sirange[dt].second and page_ids(dt) else ""}')
        for dt in DOWNLOADERS if (dt in sirange or dt in sprange) and dt in spath
    } for spath, sirange, sprange in zip(
        (sequences_paths_vid, sequences_paths_img), (virange, iirange), (vprange, iprange)))  # type: Dict[str, str]
    return base_q_v, base_q_i


def queries_from_sequences(
    sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
    sequences_pages_vid: IntSequenceMap, sequences_pages_img: IntSequenceMap,
    sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
    sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
    sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
    sequences_common_vid: StringListMap, sequences_common_img: StringListMap
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    base_q_v, base_q_i = _get_base_qs(
        sequences_ids_vid, sequences_ids_img, sequences_pages_vid, sequences_pages_img, sequences_paths_vid, sequences_paths_img)
    queries_final_vid, queries_final_img = ({
        dt: ([f'{sbase_q[dt]} {path_args(Config.dest_base, not is_vidpath, ssub[dt][i], not Config.no_date_path)} '
              f'{" ".join(normalize_ruxx_tag(tag) if dt in RUXX_DOWNLOADERS else tag for tag in ctags[dt])} '
              f'{" ".join(normalize_ruxx_tag(tag) if dt in RUXX_DOWNLOADERS else tag for tag in staglist)}'
              for i, staglist in enumerate(stags[dt]) if staglist]
             ) if dt in RUXX_DOWNLOADERS or any(any(sarg.startswith('-search') for sarg in slist) for slist in stags[dt]) else
            ([f'{sbase_q[dt]} {path_args(Config.dest_base, not is_vidpath, "", not Config.no_date_path)} '
              f'{" ".join(ctags[dt])} '
              f'-script "'
              f'{"; ".join(" ".join([f"{ssub[dt][i]}:"] + staglist) for i, staglist in enumerate(stags[dt]))}'
              f'"'] if stags[dt] else []
             )
        for dt in DOWNLOADERS
    } for sbase_q, ssub, ctags, stags, is_vidpath in
        zip((base_q_v, base_q_i), (sequences_subfolders_vid, sequences_subfolders_img), (sequences_common_vid, sequences_common_img),
            (sequences_tags_vid, sequences_tags_img), (True, False)))  # type: Dict[str, List[str]]
    return queries_final_vid, queries_final_img


def report_finals(queries_final_vid: StringListMap, queries_final_img: StringListMap) -> None:
    for ty, final_q in zip(('vid', 'img'), (queries_final_vid, queries_final_img)):
        trace(f'\nQueries {ty}:\n{NEWLINE.join(NEWLINE.join(finals) for finals in final_q.values() if finals)}', False)

#
#
#########################################
