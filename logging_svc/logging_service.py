import asyncio
import time
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger, rabbitmq_router

if sys.platform != 'win32':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

basiclogger = logger.rabbit_logger(__name__)


async def consume_mult(queue):
    while True:
        if not queue.qsize():
            await asyncio.sleep(0.001)

        else:
            # qitem = await queue.get()
            qitem = queue.get_nowait()
            try:
                jlqitem = json.loads(qitem)

                # TODO LOG DUMP
                # await write_data(file=f'{PROJ_ROOT}/captain_america_lob_messages.txt',
                #                  data=f"{json.dumps(jlqitem)}\n")

                print(jlqitem, flush=True)
            except Exception as exc:
                # print(exc.__repr__())
                print(qitem.decode(), flush=True)
                # print('nope', qitem)

            queue.task_done()
        await asyncio.sleep(0.001)


async def consume_items_from_rabbitmq(queue):
    ctr = 0
    start = time.time()
    while True:
        await asyncio.sleep(0.001)
        for method_frame, properties, body in channel.consume(queue_name, inactivity_timeout=1):
            if method_frame:
                # print(body)
                while queue.full():
                    await asyncio.sleep(0.001)
                # await queue.put(body)
                queue.put_nowait(body)
                # Acknowledge the message
                channel.basic_ack(method_frame.delivery_tag)
                ctr += 1
                if not ctr % 1000:
                    end = time.time() - start
                    # print(f'elapsed time: {end:.3f}\tmessages received: {ctr}')
            else:
                # empty remaining items from queue
                while queue.qsize():
                    await asyncio.sleep(0.001)
                end = time.time() - start
                # print(f'elapsed time: {end:.3f}\tmessages received: {ctr}')
                break
            await asyncio.sleep(0.001)

        requeued_messages = channel.cancel()


async def main():
    await asyncio.gather(consume_items_from_rabbitmq(q), consume_mult(q))


def send_test_msg(routing_keys):
    for key in routing_keys:
        level = key.split('.')[1]
        if level == 'DEBUG':
            basiclogger.debug('test DEBUG')
        elif level == 'INFO':
            basiclogger.info('test INFO')
        elif level == 'ERROR':
            basiclogger.error('test ERROR')
        elif level == 'WARNING':
            basiclogger.warning('test WARNING')
        elif level == 'CRITICAL':
            basiclogger.critical('test CRITICAL')


if __name__ == "__main__":

    # ex python logging_service.py \#.INFO \#.DEBUG
    post_parser_queue_name = sys.argv[1]
    routing_keys = sys.argv[2:]
    print(routing_keys)
    q = asyncio.Queue(maxsize=0)

    exchange_name = 'log'
    # post_parser_routing_key1 = '#'
    # post_parser_routing_key2 = 'text'

    # post_parser_queue_name = 'logger'
    queue_name = post_parser_queue_name
    # routing_key1 = post_parser_routing_key1
    # routing_key2 = post_parser_routing_key2
    time.sleep(7)

    while True:
        try:
            connection, channel = rabbitmq_router.connect_to_message_exchange(exchange_name=exchange_name,
                                                                              consumer=True,
                                                                              prefetch=500)
            # pub_queue = rabbitmq.create_queue(channel, queue_name)
            consume_queue = rabbitmq_router.create_queue(channel, queue_name)
            for routing_key in routing_keys:
                print('adding', routing_key)
                rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key)
            time.sleep(1)
            send_test_msg(routing_keys)
            # rabbitmq.bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key2)

            asyncio.run(main())
            channel.close()
            connection.close()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
            time.sleep(2)
