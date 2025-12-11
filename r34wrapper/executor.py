# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import math
import os
from asyncio import AbstractEventLoop, Future, SubprocessProtocol, as_completed, new_event_loop, sleep

from .config import Config
from .containers import CmdRunParams, DownloadCollection, Wrapper
from .defs import DOWNLOADERS, RUN_FILE_DOWNLOADERS, UTF8
from .logger import log_to, trace
from .strings import datetime_str_nfull, split_into_args
from .util import sum_lists

__all__ = ('execute', 'register_queries')


class DummyResultProtocol(SubprocessProtocol):
    def __init__(self, fut: Future) -> None:
        self.future = fut

    def process_exited(self) -> None:
        self.future.set_result(True)


executor_event_loop: Wrapper[AbstractEventLoop] = Wrapper()

queries_all: DownloadCollection[list[str]] = DownloadCollection()
dwqn_fmt = Wrapper('02d')


def register_queries(queries: DownloadCollection[list[str]]) -> None:
    queries_all.update(queries)
    max_queries_per_downloader = max(sum(len(queries[cat][dt]) for cat in queries) for dt in DOWNLOADERS)
    dwqn_fmt.reset(f'0{math.ceil(math.log10(max_queries_per_downloader + 1)):d}d')


async def run_cmd(params: CmdRunParams) -> None:
    query, dwn, dqn, dqm, cat, cqn, cqm = params.query, params.dwn, params.dqn, params.dqm, params.cat, params.cqn, params.cqm
    suffix = f'{Config.full_title}_' if Config.title else ''
    begin_msg = f'\n[{Config.full_title}] Executing \'{cat}:{dwn}\' query {cqn:d} / {cqm:d} ({dwn} query {dqn:d} / {dqm:d}):\n{query}'
    proc_file_name_body = f'{suffix}{dwn}{dqn:{dwqn_fmt.val}}_{cat.strip()}{cqn:{dwqn_fmt.val}}_{datetime_str_nfull()}'
    log_file_path = Config.dest_logs_base / f'log_{proc_file_name_body}.log'
    with open(log_file_path, 'wt+', encoding=UTF8, errors='replace', buffering=1) as log_file:
        trace(begin_msg)
        log_to(begin_msg, log_file)
        cmd_args = split_into_args(query)
        # DEBUG - do not remove
        # if DOWNLOADERS.index(dt) not in {0} or qn not in range(1, 2):
        #     return
        if dwn in RUN_FILE_DOWNLOADERS and len(query) > Config.max_cmd_len:
            run_file_path = Config.dest_run_base / f'run_{proc_file_name_body}.conf'
            trace(f'Cmdline is too long ({len(query):d}/{Config.max_cmd_len:d})! Converting to run file: {run_file_path}')
            run_file_abspath = run_file_path
            cmd_args_new = cmd_args[2:]
            cmd_args[2:] = ['file', '-path', run_file_abspath]
            with open(run_file_abspath, 'wt', encoding=UTF8, buffering=1) as run_file:
                run_file.write('\n'.join(cmd_args_new))
        ef = Future(loop=executor_event_loop.val)
        tr, _ = await executor_event_loop.val.subprocess_exec(lambda: DummyResultProtocol(ef), *cmd_args, stderr=log_file, stdout=log_file,
                                                              env={**os.environ, 'PYTHONIOENCODING': UTF8, 'PYTHONUNBUFFERED': '1'})
        await ef
        tr.close()
        log_file.seek(0)
        trace(f'\n{log_file.read()}')


async def run_cmds(dwn: str, cats: list[str], queries: list[str]) -> str | None:
    if not queries:
        return None

    assert len(cats) == len(queries)

    if dwn not in Config.downloaders:
        await sleep(1.0)  # delay this message so it isn't printed somewhere inbetween initial cmds
        trace(f'\n{dwn.upper()} SKIPPED\n')
        return None

    cats_count = len(list(filter(None, [bool(queries_all[cat][dwn]) for cat in queries_all])))

    cats_skipped = set[str]()
    cat_query_nums: dict[str, int] = dict.fromkeys(cats, 0)
    cat_query_maxs: dict[str, int] = {}
    [cat_query_maxs.update({_: len(list(filter(None, [qt_ for qt_ in cats if qt_ == _])))}) for _ in cats if _ not in cat_query_maxs]
    for query_idx in range(len(queries)):
        query = queries[query_idx]
        cat = cats[query_idx]
        cat_query_nums[cat] += 1
        if Config.test:
            continue
        if dwn in Config.disabled_downloaders.get(cat, []):
            if cat not in cats_skipped:
                cats_skipped.add(cat)
                await sleep(1.0)
                trace(f'{dwn.upper()} category \'{cat}\' was disabled! Skipped!\n')
            continue
        await run_cmd(CmdRunParams(query, dwn, query_idx + 1, len(queries), cat, cat_query_nums[cat], cat_query_maxs[cat]))
    trace(f'{dwn.upper()} COMPLETED ({cats_count - len(cats_skipped):d} / {cats_count:d} categories processed)\n')
    return dwn


async def run_all_cmds() -> None:
    if Config.no_download is True:
        trace('\n\nALL DOWNLOADERS SKIPPED DUE TO no_download FLAG!\n')
        return
    if Config.test:
        return
    enabled_dts = [dt for dt in Config.downloaders if any(bool(queries_all[cat][dt]) for cat in queries_all)]
    finished_dts: list[str] = []
    trace(f'\nRunning {len(enabled_dts):d} downloader(s): {", ".join(dt.upper() for dt in enabled_dts)}')
    trace('Working...')
    cv: Future[str | None]
    for cv in as_completed(map(
        run_cmds,
        DOWNLOADERS,
        [sum_lists([str(cat)] * len(queries_all[cat][dt]) for cat in queries_all) for dt in DOWNLOADERS],
        [sum_lists(queries_all[cat][dt] for cat in queries_all) for dt in DOWNLOADERS],
    )):
        finished_dt = await cv
        if finished_dt is None:
            continue
        finished_dts.append(finished_dt)
        trace(f'{len(finished_dts):d} / {len(enabled_dts):d} DOWNLOADERS COMPLETED: {", ".join(dt.upper() for dt in finished_dts)}')
        if remaining_dts := [dt for dt in enabled_dts if dt not in finished_dts]:
            trace(f'WAITING FOR {len(remaining_dts):d} MORE: {", ".join(dt.upper() for dt in remaining_dts)}')

    trace('ALL DOWNLOADERS FINISHED WORK\n')


def execute() -> None:
    executor_event_loop.reset(new_event_loop())
    executor_event_loop.val.run_until_complete(run_all_cmds())
    executor_event_loop.val.close()
    executor_event_loop.reset()

#
#
#########################################
