import pytest
import asyncio

from core import rabbitmq_router
from configs.base.consts import ASYNC_SLEEP
from configs.base.rabbit_connection import RABBITMQ_HOST, RABBITMQ_PORT, RABBIT_USER, RABBIT_PW

pytestmark = pytest.mark.asyncio

in_queue_name = 'test_in'
routing_key = '*.mytest'
out_queue_name = 'test_out'
exchange_name = 'message'


async def consume_during_test(queue: asyncio.Queue, channel, queue_name: str, inactivity: int = 0.001):
    try:
        await asyncio.sleep(ASYNC_SLEEP)
        for method_frame, properties, body in channel.consume(queue_name, inactivity_timeout=inactivity):
            if method_frame:
                # print(body)
                while queue.full():
                    await asyncio.sleep(ASYNC_SLEEP)
                # await queue.put(body)
                queue.put_nowait(body)
                # Acknowledge the message
                channel.basic_ack(method_frame.delivery_tag)
                break
            else:
                # queue is empty, so just add a message so this function doesnt block:
                rabbitmq_router.publish_message_to_exchange(channel=channel, exchange=exchange_name,
                                                            routing_key=routing_key,
                                                            message='test_msg')
                # empty remaining items from queue
                # while queue.qsize():
                #     await asyncio.sleep(ASYNC_SLEEP)
                # await asyncio.sleep(ASYNC_SLEEP)
    except Exception as exc:
        print(exc)
        return False
    requeued_messages = channel.cancel()
    return True


def test_connect_to_message_exchange():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost',
                                                                      port=RABBITMQ_PORT,
                                                                      exchange_name=exchange_name)
    assert channel.is_open


def test_create_queue():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', port=RABBITMQ_PORT)
    in_queue = rabbitmq_router.create_queue(channel, in_queue_name)
    assert in_queue.channel_number


def test_bind_queue_to_exchange():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', port=RABBITMQ_PORT)
    in_queue = rabbitmq_router.create_queue(channel, in_queue_name)
    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, in_queue_name, routing_key)
    assert True


def test_publish_message_to_exchange():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', port=RABBITMQ_PORT)
    in_queue = rabbitmq_router.create_queue(channel, in_queue_name)
    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, in_queue_name, routing_key)

    assert rabbitmq_router.publish_message_to_exchange(channel=channel, exchange=exchange_name, routing_key=routing_key,
                                                       message='test_msg')


async def test_consume_items_from_rabbitmq():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', port=RABBITMQ_PORT)
    in_queue = rabbitmq_router.create_queue(channel, in_queue_name)
    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, in_queue_name, routing_key)

    outqueue = asyncio.Queue()

    assert await consume_during_test(queue=outqueue, channel=channel, queue_name=in_queue_name)


async def test_publish_items_to_rabbitmq():
    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', port=RABBITMQ_PORT)
    in_queue = rabbitmq_router.create_queue(channel, in_queue_name)
    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, in_queue_name, routing_key)

    publish_queue = asyncio.Queue()
    outqueue = asyncio.Queue()

    async def publish_during_test(queue, channel, routing_key=None):
        try:
            await asyncio.sleep(ASYNC_SLEEP)
            while not queue.empty():
                # if not queue.empty():
                msg = queue.get_nowait()
                # msg = await queue.get()
                if 'exit_routing_key' in msg and 'body' in msg and not routing_key:
                    rabbitmq_router.publish_message_to_exchange(channel,
                                                                exchange_name,
                                                                routing_key=msg['exit_routing_key'],
                                                                message=msg['body'])
                else:
                    rabbitmq_router.publish_message_to_exchange(channel,
                                                                exchange_name,
                                                                routing_key=routing_key,
                                                                message=msg)
                queue.task_done()
        except Exception as exc:
            print(exc.__repr__())
            return False
        # connection.close()
        return True

    publish_queue.put_nowait({'exit_routing_key': routing_key, 'body': {'msg': 'testmsg'}})
    assert await publish_during_test(publish_queue, channel)
    publish_queue.put_nowait({'body': {'msg': 'testmsg'}})
    assert await publish_during_test(queue=publish_queue, channel=channel, routing_key=routing_key)
    assert await consume_during_test(queue=outqueue, channel=channel, queue_name=in_queue_name)
    assert await consume_during_test(queue=outqueue, channel=channel, queue_name=in_queue_name)

