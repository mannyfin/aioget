import asyncio
import time
from sys import platform

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger, rabbitmq_router
from parser_svc.parser import ParserService
from configs.base.consts import INITIAL_SLEEP

if platform != 'win32':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

basiclogger = logger.rabbit_logger(__name__)


async def main(input_queue, output_queue):
    service = ParserService(input_queue, output_queue)
    await asyncio.gather(rabbitmq_router.consume_items_from_rabbitmq(input_queue, channel, input_queue_name),
                         service.start(),
                         # no routing key provided as it will be supplied in the business configuration
                         rabbitmq_router.publish_items_to_rabbitmq(output_queue, channel, exchange_name),
                         )


if __name__ == "__main__":

    input_queue = asyncio.Queue(maxsize=2000)
    output_queue = asyncio.Queue()

    exchange_name = 'message'

    input_routing_key = 'html'  # name of the input data type
    input_queue_name = 'webpage'  # name of the sending/receiving service

    time.sleep(INITIAL_SLEEP)
    while True:
        try:
            connection, channel = rabbitmq_router.connect_to_message_exchange(exchange_name=exchange_name,
                                                                              consumer=True,
                                                                              prefetch=2000)
            # input consuming
            consume_queue = rabbitmq_router.create_queue(channel, input_queue_name)
            # output publishing

            # input bindings
            rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, input_queue_name, input_routing_key)
            # output bindings

            asyncio.run(main(input_queue, output_queue))
            channel.close()
            connection.close()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
            time.sleep(2)
