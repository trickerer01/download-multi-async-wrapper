# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Dict, List, Tuple, Optional

from defs import DOWNLOADERS, RANGE_TEMPLATES, RUXX_INDECIES, IntPair, Config, Sequence
from logger import trace
from strings import normalize_ruxx_tag, path_args, NEWLINE


def validate_sequences(sequences_ids_vid: Dict[str, Optional[Sequence]], sequences_ids_img: Dict[str, Optional[Sequence]],
                       sequences_paths_vid: Dict[str, Optional[str]], sequences_paths_img: Dict[str, Optional[str]],
                       sequences_tags_vid: Dict[str, List[List[str]]], sequences_tags_img: Dict[str, List[List[str]]],
                       sequences_subfolders_vid: Dict[str, List[str]], sequences_subfolders_img: Dict[str, List[str]],
                       python_executable: str) -> None:
    if python_executable == '':
        trace('Error: python_executable was not declared!')
        raise IOError
    for dt in DOWNLOADERS:
        ivlist = list(sequences_ids_vid[dt].ids if sequences_ids_vid[dt] else [])
        for iv in range(len(ivlist)):
            if iv > 0 and not(ivlist[iv - 1] < ivlist[iv]):
                trace(f'Error: {dt} vid ids sequence is corrupted at idx {iv - 1:d}, !({ivlist[iv - 1]:d} < {ivlist[iv]:d})!')
                raise IOError
        iilist = list(sequences_ids_img[dt].ids if sequences_ids_img[dt] else [])
        for ii in range(len(iilist)):
            if ii > 0 and not(iilist[ii - 1] < iilist[ii]):
                trace(f'Error: {dt} img ids sequence is corrupted at idx {ii - 1:d}, !({iilist[ii - 1]:d} < {iilist[ii]:d})!')
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


def report_sequences(sequences_ids_vid: Dict[str, Optional[Sequence]], sequences_ids_img: Dict[str, Optional[Sequence]],
                     sequences_paths_vid: Dict[str, Optional[str]], sequences_paths_img: Dict[str, Optional[str]],
                     sequences_tags_vid: Dict[str, List[List[str]]], sequences_tags_img: Dict[str, List[List[str]]],
                     sequences_subfolders_vid: Dict[str, List[str]], sequences_subfolders_img: Dict[str, List[str]],
                     sequences_common_vid: Dict[str, List[str]], sequences_common_img: Dict[str, List[str]],
                     python_executable: str) -> None:
    trace(f'Python executable: \'{python_executable}\'')
    [trace(f'{len([q for q in seq.values() if q]):d} {name} sequences')
     for seq, name in zip([sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img],
                          ['sequences_ids_vid', 'sequences_ids_img', 'sequences_paths_vid', 'sequences_paths_img'])]
    [trace(f'{sum(len(q) for q in seq.values() if q):d} {name} sequences')
     for seq, name in zip([sequences_tags_vid, sequences_tags_img, sequences_subfolders_vid, sequences_subfolders_img],
                          ['sequences_tags_vid', 'sequences_tags_img', 'sequences_subfolders_vid', 'sequences_subfolders_img'])]
    [trace(f'{title}:\n{NEWLINE.join(f"{item[0]}: ({len(item[1]) if item[1] else 0:d}) {str(item[1])}" for item in container.items())}')
     for title, container in zip(['Vid ids', 'Img ids', 'Vid paths', 'Img paths', 'Vid ctags', 'Img ctags', 'Vid tags', 'Img tags'],
                                 [sequences_ids_vid, sequences_ids_img, sequences_paths_vid, sequences_paths_img,
                                  sequences_common_vid, sequences_common_img, sequences_tags_vid, sequences_tags_img])]


def queries_from_sequences(sequences_ids_vid: Dict[str, Optional[Sequence]], sequences_ids_img: Dict[str, Optional[Sequence]],
                           sequences_paths_vid: Dict[str, Optional[str]], sequences_paths_img: Dict[str, Optional[str]],
                           sequences_tags_vid: Dict[str, List[List[str]]], sequences_tags_img: Dict[str, List[List[str]]],
                           sequences_subfolders_vid: Dict[str, List[str]], sequences_subfolders_img: Dict[str, List[str]],
                           sequences_common_vid: Dict[str, List[str]], sequences_common_img: Dict[str, List[str]],
                           python_executable: str,
                           config=Config) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    vrange, irange = (
        {dt: IntPair(sids[dt][:2]) for dt in DOWNLOADERS if sids[dt]} for sids in [sequences_ids_vid, sequences_ids_img]
    )  # type: Dict[str, IntPair]

    base_q_v, base_q_i = ({
        dt: (f'{python_executable} {spath[dt]} '
             f'{RANGE_TEMPLATES[dt].first % srange[dt].first} '
             f'{RANGE_TEMPLATES[dt].second % (srange[dt].second - 1)}')
        for dt in DOWNLOADERS if dt in srange.keys() and dt in spath.keys()
    } for spath, srange in zip([sequences_paths_vid, sequences_paths_img], [vrange, irange]))  # type: Dict[str, str]

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
        zip([base_q_v, base_q_i], [sequences_subfolders_vid, sequences_subfolders_img], [sequences_common_vid, sequences_common_img],
            [sequences_tags_vid, sequences_tags_img], [True, False]))  # type: Dict[str, List[str]]

    return queries_final_vid, queries_final_img


def report_finals(queries_final_vid: Dict[str, List[str]], queries_final_img: Dict[str, List[str]]) -> None:
    trace(f'\nQueries vid:\n{NEWLINE.join(NEWLINE.join(finals) for finals in queries_final_vid.values() if len(finals) > 0)}', False)
    trace(f'\nQueries img:\n{NEWLINE.join(NEWLINE.join(finals) for finals in queries_final_img.values() if len(finals) > 0)}', False)

#
#
#########################################
