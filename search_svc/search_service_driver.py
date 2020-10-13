import asyncio
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
# sys.path.insert(0, '..')
# sys.path.insert(0, '../core')

from core import logger, rabbitmq_router
from search_svc.search import SearchService
from configs.base.consts import INITIAL_SLEEP

from sys import platform, path

if platform != 'win32':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

basiclogger = logger.rabbit_logger(__name__)


async def main(input_queue, output_queue):
    try:
        service = SearchService(input_queue, output_queue)
        workers, queues, session = service.start()
        await asyncio.gather(rabbitmq_router.consume_items_from_rabbitmq(input_queue, channel, input_queue_name),
                             *workers,
                             rabbitmq_router.publish_items_to_rabbitmq(output_queue, channel, exchange_name,
                                                                       output_routing_key)
                             )
        # for queue in queues:
        #     await queue.join()
        # input_queue.join()
        # output_queue.join()
        # for consumer in workers:
        #     #canceling
        #     consumer.cancel()
        # await session.close()
    except Exception as exc:
        basiclogger.error(exc.__repr__())
        # todo return and resubmit the queues in case of catastrophic failure


if __name__ == "__main__":

    input_queue = asyncio.Queue(maxsize=200)
    output_queue = asyncio.Queue()

    exchange_name = 'message'
    input_routing_key = 'entity'
    input_queue_name = 'search'

    output_routing_key = 'url'
    output_queue_name = 'download'
    time.sleep(INITIAL_SLEEP)

    while True:
        try:
            connection, channel = rabbitmq_router.connect_to_message_exchange(exchange_name=exchange_name,
                                                                              consumer=True,
                                                                              prefetch=1000)
            consume_queue = rabbitmq_router.create_queue(channel, input_queue_name)
            publish_queue = rabbitmq_router.create_queue(channel, output_queue_name)

            rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, input_queue_name, input_routing_key)
            rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, output_queue_name, output_routing_key)

            asyncio.run(main(input_queue, output_queue))
            channel.close()
            connection.close()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
            time.sleep(2)
