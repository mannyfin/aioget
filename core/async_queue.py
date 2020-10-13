import asyncio
from typing import Any, Iterable, Callable

from configs.base.consts import ASYNC_SLEEP
from core import logger


def get_queue(maxsize: int = 0) -> asyncio.Queue:
    """
    Creates an FIFO asyncio.Queue object instance

    Args:
        maxsize (int): number of items allowed in the queue. If maxsize <= 0 the queue size is infinite

    Returns:
        asyncio.Queue instance
    """
    return asyncio.Queue(maxsize)


async def set_onto_queue(queue: asyncio.Queue, item: Any):
    """
    Pushes an item onto an asyncio.Queue

    Args:
        queue: asyncio.Queue instance
        item: Any

    Returns:
        asyncio.Queue
    """
    await queue.put(item)
    return queue


async def get_from_queue(queue: asyncio.Queue) -> Any:
    """
    Pops an item off the asyncio.Queue

    Args:
        queue: asyncio.Queue instance

    Returns:
        item from the asyncio.Queue
    """
    return await queue.get()


async def set_many_onto_queue(queue: asyncio.Queue, iterable: Iterable):
    """
    Convenience function to push multiple items onto the queue.

    Args:
        queue: asyncio.Queue
        iterable: iterable containing the items

    Returns:
        asyncio.Queue
    """
    _ = [asyncio.create_task(set_onto_queue(queue, qitem)) for qitem in iterable]
    await asyncio.gather(*_)
    return queue


async def worker(queue: asyncio.Queue, next_queue: asyncio.Queue, func: Callable, *args, **kwargs):
    while True:
        await asyncio.sleep(ASYNC_SLEEP)
        try:
            if not queue.empty():
                # print(queue._unfinished_tasks)

                # item = await get_from_queue(queue)
                if asyncio.iscoroutinefunction(func):
                    await func(queue, next_queue, *args, **kwargs)
                else:
                    func(queue, next_queue, *args, **kwargs)
        except Exception as exc:
            basiclogger.error(exc.__repr__())
        # else:
        #     break
    # return next_queue


if __name__ == '__main__':
    basiclogger = logger.rabbit_logger(__name__)
