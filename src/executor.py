# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import new_event_loop, AbstractEventLoop, as_completed, Future, SubprocessProtocol
from typing import Dict, List, Optional, Mapping, Sequence

from defs import UTF8, DOWNLOADERS, RUXX_INDECIES, Config
from logger import trace, log_to
from os import path
from strings import datetime_str_nfull, unquote

__all__ = ('queues_vid', 'queues_img', 'register_vid_queries', 'register_img_queries', 'execute')


class DummyResultProtocol(SubprocessProtocol):
    def __init__(self, fut: Future) -> None:
        self.future = fut

    def process_exited(self) -> None:
        self.future.set_result(True)


executor_event_loop = None  # type: Optional[AbstractEventLoop]

queues_vid = {dt: list() for dt in DOWNLOADERS}  # type: Dict[str, List[str]]
queues_img = {dt: list() for dt in DOWNLOADERS}  # type: Dict[str, List[str]]


def register_vid_queries(queries: Mapping[str, List[str]]) -> None:
    queues_vid.update(queries)


def register_img_queries(queries: Mapping[str, List[str]]) -> None:
    queues_img.update(queries)


def split_into_args(query: str) -> List[str]:
    """'a "b c" d "e" f g' -> ['a', 'b c', 'd', 'e', 'f', 'g']"""
    result = []  # type: List[str]
    idx1 = idx2 = idxdq = 0
    while idx2 < len(query):
        idx2 += 1
        if idx2 == len(query) - 1:
            result.append(unquote(query[idx1:]))
            break
        if query[idx2] == '"':
            if idxdq != 0:
                idx2 += 1
                result.append(unquote(query[idxdq:idx2]))
                idxdq = 0
                idx1 = idx2 + 1
            else:
                idxdq = idx2
        elif query[idx2] == ' ' and idxdq == 0:
            result.append(unquote(query[idx1:idx2]))
            idx1 = idx2 + 1

    return result


async def run_cmd(query: str, dt: str, qi: int, begin_msg: str) -> None:
    exec_time = datetime_str_nfull()
    with open(f'{Config.dest_logs_base}log_{dt}_{exec_time}.log', 'at', encoding=UTF8, buffering=True) as log_file:
        trace(begin_msg)
        log_to(begin_msg, log_file)
        trace(f'Executing cmdline {qi:d}: \'{query}\'')
        cmd_args = split_into_args(query)
        trace(f'Splitted into: \'{str(cmd_args)}\'')
        # DEBUG - do not remove
        if DOWNLOADERS.index(dt) not in {3} or qi not in range(1, 10):
            # return
            pass
        if DOWNLOADERS.index(dt) not in RUXX_INDECIES and (len(query) > Config.max_cmd_len):
            run_file_name = f'{Config.dest_run_base}run_{dt}_{exec_time}.conf'
            trace(f'Cmdline is too long ({len(query):d}/{Config.max_cmd_len:d})! Converting to run file: {run_file_name}')
            run_file_abspath = path.abspath(run_file_name)
            cmd_args_new = cmd_args[2:]
            cmd_args = cmd_args[:2] + ['file', '-path', run_file_abspath]
            trace(f'New cmd args: \'{str(cmd_args)}\'\nFile cmd args: \'{str(cmd_args_new)}\'')
            with open(run_file_abspath, 'wt', encoding=UTF8, buffering=True) as run_file:
                run_file.write('\n'.join(cmd_args_new))
        ef = Future(loop=executor_event_loop)
        tr, _ = await executor_event_loop.subprocess_exec(lambda: DummyResultProtocol(ef), *cmd_args, stderr=log_file, stdout=log_file)
        await ef
        tr.close()
    with open(f'{Config.dest_logs_base}log_{dt}_{exec_time}.log', 'rt', encoding=UTF8, buffering=True, errors='replace') as log_file:
        trace(f'\n{"".join(log_file.readlines())}')


async def run_dt_cmds(dts: Sequence[str], tys: Sequence[str], queries: Sequence[str]) -> None:
    assert all(dt == dts[0] for dt in dts)
    dt = dts[0]

    if dt not in Config.downloaders:
        trace(f'\n{dt.upper()} SKIPPED\n')
        return

    qis = [0, 0]
    for qi in range(len(queries)):
        q_idx = 1 - int(tys[qi] == 'vid')
        qis[q_idx] += 1
        await run_cmd(queries[qi], dt, qi, f'\nExecuting {dt} {tys[qi]} query {qis[q_idx]:d}:\n{queries[qi]}')
    trace(f'{dt.upper()} COMPLETED\n')


async def run_all_cmds() -> None:
    if Config.no_download is True:
        trace('\n\nALL DOWNLOADERS SKIPPED DUE TO no_download FLAG!\n')
        return

    for cv in as_completed([run_dt_cmds(dts, tys, queries) for dts, tys, queries in
                            zip([[dt] * (len(queues_vid[dt]) + len(queues_img[dt])) for dt in DOWNLOADERS],
                                [['vid'] * len(queues_vid[dt]) + ['img'] * len(queues_img[dt]) for dt in DOWNLOADERS],
                                [queues_vid[dt] + queues_img[dt] for dt in DOWNLOADERS])], loop=executor_event_loop):
        await cv
    trace('ALL DOWNLOADERS FINISHED WORK\n')


def execute() -> None:
    global executor_event_loop
    executor_event_loop = new_event_loop()
    executor_event_loop.run_until_complete(run_all_cmds())
    executor_event_loop.close()
    executor_event_loop = None

#
#
#########################################
