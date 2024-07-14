# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import AbstractEventLoop, Future, SubprocessProtocol, new_event_loop, sleep, as_completed
from math import log10, ceil
from os import path
from typing import Dict, List, Optional, Sequence, Iterable, Any

from defs import DownloadCollection, Wrapper, Config, UTF8, DOWNLOADERS, RUN_FILE_DOWNLOADERS
from logger import trace, log_to
from strings import datetime_str_nfull, unquote

__all__ = ('queries_all', 'register_queries', 'execute')


class DummyResultProtocol(SubprocessProtocol):
    def __init__(self, fut: Future) -> None:
        self.future = fut

    def process_exited(self) -> None:
        self.future.set_result(True)


executor_event_loop: Wrapper[Optional[AbstractEventLoop]] = Wrapper()

queries_all: DownloadCollection[List[str]] = DownloadCollection()
dtqn_fmt = Wrapper('02d')


def sum_lists(lists: Iterable[Iterable[Any]]) -> list:
    total = list()
    [total.extend(li) for li in lists]
    return total


def register_queries(queries: DownloadCollection[List[str]]) -> None:
    queries_all.update(queries)
    max_queries_per_downloader = max(sum(len(queries[cat][dt]) for cat in queries) for dt in DOWNLOADERS)
    dtqn_fmt.reset(f'0{int(ceil(log10(max_queries_per_downloader + 1))):d}d')


def split_into_args(query: str) -> List[str]:
    r"""'a "b c" d "e" f g "{\\"h\\":\\"j\\",\\"k\\":\\"l\\"}"' -> ['a', 'b c', 'd', 'e', 'f', 'g', '{"h":"j","k":"l"}]"""
    def append_result(res_str: str) -> None:
        res_str = unquote(res_str.replace('\\"', '\u2033')).replace('\u2033', '"')
        result.append(res_str)

    result = []
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


async def run_cmd(query: str, dt: str, qn: int, qt: str, qtn: int) -> None:
    exec_time = datetime_str_nfull()
    suffix = f'{Config.fulltitle}_' if Config.title else ''
    begin_msg = f'\n[{Config.fulltitle}] Executing \'{qt}\' {dt} query {qtn:d} ({dt} query {qn:d}):\n{query}'
    log_file_name = f'{Config.dest_logs_base}log_{suffix}{dt}{qn:{dtqn_fmt()}}_{qt.strip()}{qtn:{dtqn_fmt()}}_{exec_time}.log'
    with open(log_file_name, 'wt+', encoding=UTF8, errors='replace', buffering=1) as log_file:
        trace(begin_msg)
        log_to(begin_msg, log_file)
        cmd_args = split_into_args(query)
        # DEBUG - do not remove
        # if DOWNLOADERS.index(dt) not in {0} or qn not in range(1, 2):
        #     return
        if dt in RUN_FILE_DOWNLOADERS and len(query) > Config.max_cmd_len:
            run_file_name = f'{Config.dest_run_base}run_{suffix}{dt}{qn:{dtqn_fmt()}}_{qt.strip()}{qtn:{dtqn_fmt()}}_{exec_time}.conf'
            trace(f'Cmdline is too long ({len(query):d}/{Config.max_cmd_len:d})! Converting to run file: {run_file_name}')
            run_file_abspath = path.abspath(run_file_name)
            cmd_args_new = cmd_args[2:]
            cmd_args[2:] = ['file', '-path', run_file_abspath]
            with open(run_file_abspath, 'wt', encoding=UTF8, buffering=1) as run_file:
                run_file.write('\n'.join(cmd_args_new))
        ef = Future(loop=executor_event_loop())
        tr, _ = await executor_event_loop().subprocess_exec(lambda: DummyResultProtocol(ef), *cmd_args, stderr=log_file, stdout=log_file)
        await ef
        tr.close()
        log_file.seek(0)
        trace(f'\n{log_file.read()}')


async def run_dt_cmds(dt: str, qts: Sequence[str], queries: Sequence[str]) -> None:
    if not queries:
        return

    assert len(qts) == len(queries)

    if dt not in Config.downloaders:
        await sleep(1.0)  # delay this message so it isn't printed somewhere inbetween initial cmds
        trace(f'\n{dt.upper()} SKIPPED\n')
        return

    qt_skips = set()
    qns: Dict[str, int] = {qt: 0 for qt in qts}
    for qi, qt in enumerate(qts):
        qns[qt] += 1
        if Config.test:
            continue
        if qt in Config.disabled_downloaders and dt in Config.disabled_downloaders[qt]:
            if qt not in qt_skips:
                qt_skips.add(qt)
                await sleep(1.0)
                trace(f'{dt.upper()} category \'{qt}\' was disabled! Skipped!\n')
            continue
        await run_cmd(queries[qi], dt, qi + 1, qt, qns[qt])
    trace(f'{dt.upper()} COMPLETED ({len(queries_all) - len(qt_skips):d} / {len(queries_all):d} categories processed)\n')


async def run_all_cmds() -> None:
    if Config.no_download is True:
        trace('\n\nALL DOWNLOADERS SKIPPED DUE TO no_download FLAG!\n')
        return
    for cv in as_completed(map(
        run_dt_cmds,
        [dt for dt in DOWNLOADERS],
        [sum_lists([cat] * len(queries_all[cat][dt]) for cat in queries_all) for dt in DOWNLOADERS],
        [sum_lists(queries_all[cat][dt] for cat in queries_all) for dt in DOWNLOADERS]
    )):
        await cv
    trace('ALL DOWNLOADERS FINISHED WORK\n')


def execute() -> None:
    executor_event_loop.reset(new_event_loop())
    executor_event_loop().run_until_complete(run_all_cmds())
    executor_event_loop().close()
    executor_event_loop.reset()

#
#
#########################################
