# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import new_event_loop, AbstractEventLoop, as_completed, Future, SubprocessProtocol
from typing import Dict, List, Optional

from defs import __DEBUG__, UTF8, DOWNLOADERS, Config
from logger import trace, log_to
from strings import datetime_str_nfull, unquote


class DummyResultProtocol(SubprocessProtocol):
    def __init__(self, fut: Future) -> None:
        self.future = fut

    def process_exited(self) -> None:
        self.future.set_result(True)


executor_event_loop = None  # type: Optional[AbstractEventLoop]

queues_vid = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]
queues_img = {dt: [] for dt in DOWNLOADERS}  # type: Dict[str, List[str]]


def register_vid_queries(queries: Dict[str, List[str]]) -> None:
    queues_vid.update(queries)


def register_img_queries(queries: Dict[str, List[str]]) -> None:
    queues_img.update(queries)


def split_into_args(query: str) -> List[str]:
    """
    'a "b c" d "e" f g' -> ['a', 'b c', 'd', 'e', 'f', 'g']
    """
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
    with open(f'{Config.DEST_LOGS_BASE}log_{dt}_{exec_time}.log', 'at', encoding=UTF8, buffering=True) as log_file:
        trace(begin_msg)
        log_to(begin_msg, log_file)
        trace(f'Executing cmdline: \'{query}\'')
        cmd_args = split_into_args(query)
        trace(f'Splitted into: \'{str(cmd_args)}\'')
        if __DEBUG__:
            if DOWNLOADERS.index(dt) not in [0, 1] or qi not in range(0, 90):
                return
                pass
        ef = Future(loop=executor_event_loop)
        tr, _ = await executor_event_loop.subprocess_exec(lambda: DummyResultProtocol(ef), *cmd_args, stderr=log_file, stdout=log_file)
        await ef
        tr.close()
    with open(f'{Config.DEST_LOGS_BASE}log_{dt}_{exec_time}.log', 'rt', encoding=UTF8, buffering=True) as log_file:
        trace(f'\n{"".join(log_file.readlines())}')


async def run_dt_cmds(dts: List[str], tys: List[str], queries: List[str]) -> None:
    assert all(dt == dts[0] for dt in dts)
    vts = its = 0
    for qi in range(len(queries)):
        is_vid_q = tys[qi] == 'vid'
        if is_vid_q:
            vts += 1
        else:
            its += 1
        await run_cmd(queries[qi], dts[0], qi, f'\nExecuting {dts[0]} {tys[qi]} query {vts if is_vid_q else its:d}:\n{queries[qi]}')
    trace(f'{dts[0].upper()} COMPLETED\n')


async def run_all_cmds() -> None:
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
