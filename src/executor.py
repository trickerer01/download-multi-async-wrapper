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
from collections.abc import Iterable

from config import Config
from containers import DownloadCollection, Wrapper
from defs import DOWNLOADERS, RUN_FILE_DOWNLOADERS, UTF8
from logger import log_to, trace
from strings import datetime_str_nfull, normalize_path, unquote

__all__ = ('execute', 'register_queries')


class DummyResultProtocol(SubprocessProtocol):
    def __init__(self, fut: Future) -> None:
        self.future = fut

    def process_exited(self) -> None:
        self.future.set_result(True)


executor_event_loop: Wrapper[AbstractEventLoop] = Wrapper()

queries_all: DownloadCollection[list[str]] = DownloadCollection()
dtqn_fmt = Wrapper('02d')


def sum_lists(lists: Iterable[Iterable[str]]) -> list[str]:
    total = []
    [total.extend(li) for li in lists]
    return total


def register_queries(queries: DownloadCollection[list[str]]) -> None:
    queries_all.update(queries)
    max_queries_per_downloader = max(sum(len(queries[cat][dt]) for cat in queries) for dt in DOWNLOADERS)
    dtqn_fmt.reset(f'0{math.ceil(math.log10(max_queries_per_downloader + 1)):d}d')


def split_into_args(query: str) -> list[str]:
    r"""'a "b c" d "e" f g "{\\"h\\":\\"j\\",\\"k\\":\\"l\\"}"' -> ['a', 'b c', 'd', 'e', 'f', 'g', '{"h":"j","k":"l"}']"""
    def append_result(res_str: str) -> None:
        res_str = unquote(res_str.replace('\\"', '\u2033')).replace('\u2033', '"')
        result.append(res_str)

    result: list[str] = []
    idx1 = idx2 = idxdq = 0
    while idx2 < len(query):
        idx2 += 1
        if idx2 == len(query) - 1:
            result.append(unquote(query[idx1:]))
            break
        if query[idx2] == '"':
            if idx2 == 0 or query[idx2 - 1] != '\\':
                if idxdq != 0:
                    idx2 += 1
                    append_result(query[idxdq:idx2])
                    idxdq = 0
                    idx1 = idx2 + 1
                else:
                    idxdq = idx2
        elif query[idx2] == ' ' and idxdq == 0:
            append_result(query[idx1:idx2])
            idx1 = idx2 + 1
    return result


async def run_cmd(query: str, dt: str, qn: int, qm: int, qt: str, qtn: int, qtm: int) -> None:
    suffix = f'{Config.full_title}_' if Config.title else ''
    begin_msg = f'\n[{Config.full_title}] Executing \'{qt}\' {dt} query {qtn:d} / {qtm:d} ({dt} query {qn:d} / {qm:d}):\n{query}'
    proc_file_name_body = f'{suffix}{dt}{qn:{dtqn_fmt.val}}_{qt.strip()}{qtn:{dtqn_fmt.val}}_{datetime_str_nfull()}'
    log_file_name = f'{Config.dest_logs_base}log_{proc_file_name_body}.log'
    with open(log_file_name, 'wt+', encoding=UTF8, errors='replace', buffering=1) as log_file:
        trace(begin_msg)
        log_to(begin_msg, log_file)
        cmd_args = split_into_args(query)
        # DEBUG - do not remove
        # if DOWNLOADERS.index(dt) not in {0} or qn not in range(1, 2):
        #     return
        if dt in RUN_FILE_DOWNLOADERS and len(query) > Config.max_cmd_len:
            run_file_name = f'{Config.dest_run_base}run_{proc_file_name_body}.conf'
            trace(f'Cmdline is too long ({len(query):d}/{Config.max_cmd_len:d})! Converting to run file: {run_file_name}')
            run_file_abspath = normalize_path(os.path.abspath(run_file_name), False)
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


async def run_dt_cmds(dt: str, qts: list[str], queries: list[str]) -> str | None:
    if not queries:
        return None

    assert len(qts) == len(queries)

    if dt not in Config.downloaders:
        await sleep(1.0)  # delay this message so it isn't printed somewhere inbetween initial cmds
        trace(f'\n{dt.upper()} SKIPPED\n')
        return None

    dt_qt_num = len(list(filter(None, [bool(queries_all[dcat][dt]) for dcat in queries_all])))

    qt_skips = set()
    qns: dict[str, int] = dict.fromkeys(qts, 0)
    qms: dict[str, int] = {}
    [qms.update({_: len(list(filter(None, [qt_ for qt_ in qts if qt_ == _])))}) for _ in qts if _ not in qms]
    for qi, qt in enumerate(qts):
        qns[qt] += 1
        if Config.test:
            continue
        if dt in Config.disabled_downloaders.get(qt, []):
            if qt not in qt_skips:
                qt_skips.add(qt)
                await sleep(1.0)
                trace(f'{dt.upper()} category \'{qt}\' was disabled! Skipped!\n')
            continue
        await run_cmd(queries[qi], dt, qi + 1, len(qts), qt, qns[qt], qms[qt])
    trace(f'{dt.upper()} COMPLETED ({dt_qt_num - len(qt_skips):d} / {dt_qt_num:d} categories processed)\n')
    return dt


async def run_all_cmds() -> None:
    if Config.no_download is True:
        trace('\n\nALL DOWNLOADERS SKIPPED DUE TO no_download FLAG!\n')
        return
    if Config.test:
        return
    enabled_dts = [dt for dt in Config.downloaders if any(bool(queries_all[cat][dt]) for cat in queries_all)]
    finished_dts = list[str]()
    trace(f'\nRunning {len(enabled_dts)} downloader(s): {", ".join(dt.upper() for dt in enabled_dts)}')
    trace('Working...')
    cv: Future[str | None]
    for cv in as_completed(map(
        run_dt_cmds,
        list(DOWNLOADERS),
        [sum_lists([str(cat)] * len(queries_all[cat][dt]) for cat in queries_all) for dt in DOWNLOADERS],
        [sum_lists(queries_all[cat][dt] for cat in queries_all) for dt in DOWNLOADERS],
    )):
        finished_dt = await cv
        if finished_dt is None:
            continue
        finished_dts.append(finished_dt)
        trace(f'{len(finished_dts)} / {len(enabled_dts)} DOWNLOADERS COMPLETED: {", ".join(dt.upper() for dt in finished_dts)}')
        if remaining_dts := [dt for dt in enabled_dts if dt not in finished_dts]:
            trace(f'WAITING FOR {len(remaining_dts)} MORE: {", ".join(dt.upper() for dt in remaining_dts)}')

    trace('ALL DOWNLOADERS FINISHED WORK\n')


def execute() -> None:
    executor_event_loop.reset(new_event_loop())
    executor_event_loop.val.run_until_complete(run_all_cmds())
    executor_event_loop.val.close()
    executor_event_loop.reset()

#
#
#########################################
