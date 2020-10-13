import asyncio
import time

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger, rabbitmq_router
from download_svc.download import DownloadService
from configs.base.consts import INITIAL_SLEEP

from sys import platform

if platform != 'win32':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

basiclogger = logger.rabbit_logger(__name__)


async def main(input_queue, output_queue):
    try:
        service = DownloadService(input_queue, output_queue)
        workers, queues, session = service.start()
        await asyncio.gather(rabbitmq_router.consume_items_from_rabbitmq(input_queue, channel, input_queue_name),
                             *workers,
                             rabbitmq_router.publish_items_to_rabbitmq(output_queue, channel, exchange_name,
                                                                       output_routing_key),
                             # rabbitmq.publish_items_to_rabbitmq(output_queue, channel, exchange_name, snapshot_routing_key),
                             )
        # for queue in queues:
        #     await queue.join()
        # input_queue.join()
        # output_queue.join()
        # for consumer in workers:
        #     canceling
        # consumer.cancel()
        # await session.close()
    except Exception as exc:
        basiclogger.error(exc.__repr__())


if __name__ == "__main__":

    input_queue = asyncio.Queue(maxsize=200)
    output_queue = asyncio.Queue()

    exchange_name = 'message'

    input_routing_key = 'url'  # name of the input data type
    input_queue_name = 'download'  # name of the sending/receiving service

    output_routing_key = 'html'  # name of the output data type
    output_queue_name = 'webpage'  # name of the sending/receiving service
    time.sleep(INITIAL_SLEEP)

    while True:
        try:
            connection, channel = rabbitmq_router.connect_to_message_exchange(exchange_name=exchange_name,
                                                                              consumer=True,
                                                                              prefetch=1000)
            # input consuming
            consume_queue = rabbitmq_router.create_queue(channel, input_queue_name)
            # output publishing
            publish_queue_1 = rabbitmq_router.create_queue(channel, output_queue_name)
            # publish_queue_2 = rabbitmq.create_queue(channel, snapshot_queue_name)

            # input bindings
            rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, input_queue_name, input_routing_key)
            # output bindings

            # connection, channel = rabbitmq.connect_to_message_exchange(exchange_name=exchange_name, consumer=False,
            #                                                            )
            rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, output_queue_name, output_routing_key)
            # rabbitmq.bind_queue_to_exchange(channel, exchange_name, snapshot_queue_name, snapshot_routing_key)

            asyncio.run(main(input_queue, output_queue))
            channel.close()
            connection.close()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
            time.sleep(2)
