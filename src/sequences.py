# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile
from subprocess import check_output
from typing import Dict, List, Set, Tuple, Optional, Mapping, Sequence, TypeVar

from defs import DOWNLOADERS, RANGE_TEMPLATES, RUXX_INDECIES, APP_NAMES, IntPair, Config, IntSequence
from logger import trace
from strings import normalize_ruxx_tag, path_args, NEWLINE

__all__ = ('validate_sequences', 'report_sequences', 'queries_from_sequences_base', 'queries_from_sequences', 'report_finals')

IntSequenceMap = TypeVar('IntSequenceMap', bound=Mapping[str, Optional[IntSequence]])
StringMap = TypeVar('StringMap', bound=Mapping[str, Optional[str]])
StringListMap = TypeVar('StringListMap', bound=Mapping[str, Sequence[str]])
StringListListMap = TypeVar('StringListListMap', bound=Mapping[str, Sequence[List[str]]])


def validate_sequences(
        sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
        sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
        sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
        sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
        sequences_paths_update: StringMap, python_executable: str) -> None:
    if not python_executable:
        trace('Error: python_executable was not declared!')
        raise IOError
    for dt in DOWNLOADERS:
        ivlist = list(sequences_ids_vid[dt].ids if sequences_ids_vid[dt] else [])
        for iv in range(len(ivlist)):
            if iv > 0 and ivlist[iv - 1] >= ivlist[iv]:
                trace(f'Error: {dt} vid ids sequence is corrupted at idx {iv - 1:d}, {ivlist[iv - 1]:d} >= {ivlist[iv]:d}!')
                raise IOError
        iilist = list(sequences_ids_img[dt].ids if sequences_ids_img[dt] else [])
        for ii in range(len(iilist)):
            if ii > 0 and iilist[ii - 1] >= iilist[ii]:
                trace(f'Error: {dt} img ids sequence is corrupted at idx {ii - 1:d}, {iilist[ii - 1]:d} >= {iilist[ii]:d}!')
                raise IOError
        if (not not sequences_paths_vid[dt]) != (not not sequences_ids_vid[dt]):
            trace(f'Error: sequence list existance for vid tags/ids mismatch for {dt}!')
            raise IOError
        if (not not sequences_paths_img[dt]) != (not not sequences_ids_img[dt]):
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
        out_py = check_output((python_executable, '-V'))
        out_py_str = out_py.decode().strip()
        match_py_ver = re_py_ver.fullmatch(out_py_str)
        assert match_py_ver
        assert (int(match_py_ver.group(1)), int(match_py_ver.group(2))) >= (3, 7), 'Minimum python version required is 3.7!'
        trace(f'Found python {".".join(match_py_ver.groups())}')
    except Exception:
        trace(f'Error: invalid python executable!')
        raise IOError
    checked_downloaders = set()  # type: Set[str]
    for seq, ch in zip((sequences_paths_vid, sequences_paths_img), ('v', 'i')):
        for dt in seq:
            dpath = seq[dt]  # type: Optional[str]
            if not dpath:
                continue
            if dt in checked_downloaders:
                continue
            checked_downloaders.add(dt)
            try:
                trace(f'Looking for {dt}({ch}) downloader...')
                out_d = check_output((python_executable, dpath, '--version'))
                out_d_str = out_d.decode().strip()
                assert out_d_str.startswith(APP_NAMES[dt]), f'Unexpected output for {dt}({ch}): {out_d_str[:min(len(out_d_str), 20)]}!'
            except Exception:
                trace(f'Error: invalid {dt}({ch}) downloader found at: \'{dpath}\'!')
                raise IOError
    if Config.update:
        for dt in sequences_paths_update:
            upath = sequences_paths_update[dt]  # type: Optional[str]
            if not upath:
                continue
            try:
                trace(f'Looking for {dt} updater...')
                out_u = check_output((python_executable, upath, '--version'))
                out_u_str = out_u.decode().strip()
                assert out_u_str.startswith(APP_NAMES[dt]), f'Unexpected output for {dt}: {out_u_str[:min(len(out_u_str), 20)]}!'
            except Exception:
                trace(f'Error: invalid {dt} updater found at: \'{upath}\'!')
                raise IOError


def report_sequences(
        sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
        sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
        sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
        sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
        sequences_common_vid: StringListMap, sequences_common_img: StringListMap,
        python_executable: str) -> None:
    trace(f'Python executable: \'{python_executable}\'')
    [trace(f'{len([q for q in seq.values() if q]):d} {name} sequences')
     for seq, name in zip((sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img),
                          ('sequences_ids_vid', 'sequences_ids_img', 'sequences_paths_vid', 'sequences_paths_img'))]
    [trace(f'{sum(len(q) for q in seq.values() if q):d} {name} sequences')
     for seq, name in zip((sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img),
                          ('sequences_tags_vid', 'sequences_tags_img', 'sequences_subfolders_vid', 'sequences_subfolders_img'))]
    [trace(f'{title}:\n{NEWLINE.join(f"{item[0]}: ({len(item[1]) if item[1] else 0:d}) {str(item[1])}" for item in container.items())}')
     for title, container in zip(('Vid ids', 'Img ids', 'Vid paths', 'Img paths', 'Vid ctags', 'Img ctags', 'Vid tags', 'Img tags'),
                                 (sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
                                  sequences_common_vid, sequences_common_img, sequences_tags_vid, sequences_tags_img))]


def _get_base_qs(
        sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
        sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
        python_executable: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    vrange, irange = (
        {dt: IntPair(sids[dt][:2]) for dt in DOWNLOADERS if sids[dt]} for sids in (sequences_ids_vid, sequences_ids_img)
    )  # type: Dict[str, IntPair]
    base_q_v, base_q_i = ({
        dt: (f'{python_executable} "{spath[dt]}" '
             f'{RANGE_TEMPLATES[dt].first % srange[dt].first} '
             f'{RANGE_TEMPLATES[dt].second % (srange[dt].second - 1)}')
        for dt in DOWNLOADERS if dt in srange.keys() and dt in spath.keys()
    } for spath, srange in zip((sequences_paths_vid, sequences_paths_img), (vrange, irange)))  # type: Dict[str, str]
    return base_q_v, base_q_i


def queries_from_sequences_base(
        sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
        sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
        sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
        sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
        sequences_common_vid: StringListMap, sequences_common_img: StringListMap,
        python_executable: str, config=Config) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    base_q_v, base_q_i = _get_base_qs(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img, python_executable)
    queries_final_vid, queries_final_img = ({
        dt: ([f'{sbase_q[dt]} {path_args(config.dest_base, not is_vidpath, ssub[dt][i])} '
              f'{" ".join(normalize_ruxx_tag(tag) if DOWNLOADERS.index(dt) in RUXX_INDECIES else tag for tag in ctags[dt])} '
              f'{" ".join(normalize_ruxx_tag(tag) if DOWNLOADERS.index(dt) in RUXX_INDECIES else tag for tag in staglist)}'
              for i, staglist in enumerate(stags[dt]) if len(staglist) > 0])
        for dt in DOWNLOADERS
    } for sbase_q, ssub, ctags, stags, is_vidpath in
        zip((base_q_v, base_q_i), (sequences_subfolders_vid, sequences_subfolders_img), (sequences_common_vid, sequences_common_img),
            (sequences_tags_vid, sequences_tags_img), (True, False)))  # type: Dict[str, List[str]]
    return queries_final_vid, queries_final_img


def queries_from_sequences(
        sequences_ids_vid: IntSequenceMap, sequences_ids_img: IntSequenceMap,
        sequences_paths_vid: StringMap, sequences_paths_img: StringMap,
        sequences_tags_vid: StringListListMap, sequences_tags_img: StringListListMap,
        sequences_subfolders_vid: StringListMap, sequences_subfolders_img: StringListMap,
        sequences_common_vid: StringListMap, sequences_common_img: StringListMap,
        python_executable: str, config=Config) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    base_q_v, base_q_i = _get_base_qs(sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img, python_executable)
    queries_final_vid, queries_final_img = ({
        dt: ([f'{sbase_q[dt]} {path_args(config.dest_base, not is_vidpath, ssub[dt][i])} '
              f'{" ".join(normalize_ruxx_tag(tag) for tag in ctags[dt])} '
              f'{" ".join(normalize_ruxx_tag(tag) for tag in staglist)}'
              for i, staglist in enumerate(stags[dt]) if len(staglist) > 0]
             ) if DOWNLOADERS.index(dt) in RUXX_INDECIES else
            ([f'{sbase_q[dt]} {path_args(config.dest_base, not is_vidpath, "")} '
              f'{" ".join(ctags[dt])} '
              f'-script "'
              f'{"; ".join(" ".join([f"{ssub[dt][i]}:"] + staglist) for i, staglist in enumerate(stags[dt]))}'
              f'"'] if len(stags[dt]) > 0 else []
             )
        for dt in DOWNLOADERS
    } for sbase_q, ssub, ctags, stags, is_vidpath in
        zip((base_q_v, base_q_i), (sequences_subfolders_vid, sequences_subfolders_img), (sequences_common_vid, sequences_common_img),
            (sequences_tags_vid, sequences_tags_img), (True, False)))  # type: Dict[str, List[str]]
    return queries_final_vid, queries_final_img


def report_finals(queries_final_vid: StringListMap, queries_final_img: StringListMap) -> None:
    [trace(f'\nQueries {ty}:\n{NEWLINE.join(NEWLINE.join(finals) for finals in final_q.values() if len(finals) > 0)}', False)
     for ty, final_q in zip(('vid', 'img'), (queries_final_vid, queries_final_img))]

#
#
#########################################
