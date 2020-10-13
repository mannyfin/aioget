import os
from pathlib import Path
import shutil
import json
import asyncio
import concurrent.futures
from functools import partial
from datetime import datetime, timedelta
from typing import Union, List, Coroutine, Callable, Tuple, Optional
from multiprocessing import cpu_count
import pickle

from deprecated.sphinx import deprecated
from configs.base import consts
from core import logger

basiclogger = logger.rabbit_logger(__name__)


def pop_arb_field_if_exists(msg: dict) -> Tuple[dict, dict]:
    """values in the arb field exepected to be a dictionary."""
    if 'arb' in msg:
        arb = msg.pop('arb')
        return arb, msg
    return {}, msg


def set_arb(msg: dict, arb: dict) -> dict:
    if arb:
        msg['arb'] = arb
    return msg


def load_config(path: str) -> dict:
    """
    Provide path to load the JSON config

    Args:
        path: str, should be path to JSON file

    Returns:
        Any JSON-serializable data. Usually a dict for the config files.
    """
    with open(path, 'r') as f:
        config = json.load(f)
    return config


def make_config(paths):
    configs = {}
    for fp in paths:
        business_driver = Path(fp).parent.stem #os.path.split(fp[0])[1] #fp.rsplit('/', 2)[1]
        if business_driver not in configs:
            configs[business_driver] = {}
        newconfig = load_config(fp)
        for key, val in newconfig.items():
            configs[business_driver][key] = val
    return configs


def load_model(path: str, mode: str = 'rb', response_encoding=None):
    with open(path, mode) as f:
        model = pickle.load(f)
    return model


def merge_configs(driver: dict, client: dict) -> dict:
    """
    Merge Driver and Client config. The Client configs will overwrite matching keys in the Driver config.

    Args:
        driver (dict): driver dictionary of configs
        client (dict): client dictionary of configs

    Returns:
        Merged configs (dict)
    """
    return {**driver, **client}


# def process_pool(workers: int,
#                  func: Callable,
#                  iterable: Union[list, tuple, asyncio.Queue]) -> List[Coroutine]:
#     """
#     Pass an iterable to a process pool and return a list of asyncio futures.
#
#     Args:
#         workers: Number of workers in the Process Pool
#         func: function
#         iterable: unique values you will pass to each process
#         args: additional values passed to every process
#         kwargs: additional values passed to every process
#
#     Returns:
#         List of asyncio.Futures
#
#     Examples:
#
#         .. code-block:: python
#             :linenos:
#
#             def cpu_bound_func(a, b=b):
#                 # CPU-bound operations will block the event loop:
#                 # in general it is preferable to run them in a
#                 # process pool. Simulating this. with arg and kwarg.
#                 time.sleep(1)
#                 return a**2, b*-1
#
#             def async_process_pool(workers: int, func: Callable, iterable, *args, **kwargs) -> list:
#                 if workers <= 0:
#                     workers = cpu_count()
#                 loop = asyncio.get_running_loop()
#                 with concurrent.futures.ProcessPoolExecutor(workers) as pool:
#                     return [loop.run_in_executor(pool, partial(func, _ , *args, **kwargs)) for _ in iterable]
#
#             # submitting futures to the process pool and getting results as completed. Not necessarily in order.
#             async def exhaust_async_process_pool():
#                 for _ in asyncio.as_completed(async_process_pool(0, cpu_bound_func, list(range(8)), b=2)):
#                     result = await _
#                     print(result)
#
#             start = time.time()
#             asyncio.run(exhaust_async_process_pool())
#             end = time.time() - start
#             print(end)  # should take a littler longer than math.ceil(8/workers) due to process overhead.
#
#
#         Output:
#
#             (1, -2)
#             (0, -2)
#             (9, -2)
#             (4, -2)
#             (16, -2)
#             (25, -2)
#             (36, -2)
#
#         .. todo:: make this work with async queues correctly...
#     """
#     if workers <= 0:
#         workers = cpu_count()
#     loop = asyncio.get_running_loop()
#     with concurrent.futures.ProcessPoolExecutor(workers) as pool:
#         if isinstance(iterable, (list, tuple)):
#             return [loop.run_in_executor(pool, partial(func, **value)) for value in iterable]
#         elif isinstance(iterable, asyncio.Queue):
#             # todo make this work
#             futures = []
#             for ctr in range(iterable.qsize()):
#                 value = iterable.get_nowait()
#                 futures.append(loop.run_in_executor(pool, partial(func, **value)))
#                 iterable.task_done()
#             return futures


async def parse_consumer(next_queue: asyncio.Queue, write_queue: asyncio.Queue,
                         func: Optional[Callable] = None):
    """
    Parses the response html in a concurrent.futures.ProcessPoolExcecutor Process Pool. This function checks if
    next_queue is empty. If it is not, then it empties it by getting each item in next_queue and passing to the
    Process Pool and returing a future. The future is then put on the write_queue.

    If queue's requests are completed and next_queue has completed (i.e. no unfinished tasks in either queue),
    then break.

    .. todo:: this could be refactored by async_queue.worker

    Args:
        next_queue: queue containing the responses
        write_queue: queue to put the list of asyncio.Futures on
        queue: queue containing the requests to be made. It is used to know when to finish this task
        func: function to use in the process pool. This is self.parse

    Returns:
        None
    """
    pool = concurrent.futures.ProcessPoolExecutor(max(cpu_count(), 8))
    # pool = concurrent.futures.ProcessPoolExecutor(1)  # useful for debugging

    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(consts.ASYNC_SLEEP)
        if not next_queue.empty():

            value = await next_queue.get()
            if not func:
                func = value.pop('parse_func')
            futs = loop.run_in_executor(pool, partial(func, **value))
            await write_queue.put(futs)
            func = None
            # futures.append(loop.run_in_executor(pool, partial(func, **value)))

            next_queue.task_done()
        # if not queue._unfinished_tasks and not next_queue._unfinished_tasks:
        #     break
    pool.shutdown()  # not very useful...
