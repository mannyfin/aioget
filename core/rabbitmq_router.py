"""
Helper functions for using RabbitMQ
"""
import asyncio
import sys
import json
from typing import Optional

import pika

from configs.base.consts import ASYNC_SLEEP
from configs.base.rabbit_connection import RABBITMQ_HOST, RABBITMQ_PORT, RABBIT_USER, RABBIT_PW

from sys import platform
if platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def connect_to_message_exchange(host: str = RABBITMQ_HOST, exchange_name: str = 'message',
                                exchange_type: str = 'topic', consumer: bool = False, prefetch: int = 100,
                                port=RABBITMQ_PORT, **kwargs):
    """
    Make connection to an exchange using a Blocking Connection.
    .. todo: change to use async

    Args:
        port:
        prefetch:
        consumer:
        host:
        exchange_name:
        exchange_type:

    Returns:
        connection: connection to channel (used for when you want to do connection.close()
        channel: connection channel (used to publish/consume messages to/from exchange)
    """
    # print(host) #prints the hostname rabbit
    credentials = pika.PlainCredentials(username=RABBIT_USER, password=RABBIT_PW)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=credentials,
                                                                   **kwargs))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
    if consumer:
        channel.basic_qos(prefetch_count=prefetch)

    return connection, channel


def create_queue(channel, queue_name: str, exclusive: bool = False, durable: bool = True):
    queue = channel.queue_declare(queue_name, exclusive=exclusive, durable=durable, auto_delete=False)
    return queue


def bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key):
    return channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)


def publish_message_to_exchange(channel, exchange, routing_key, message, headers=None) -> bool:
    if channel is None or not channel.is_open:
        return False
    try:
        if not headers:
            headers = {}  # {'a': 'b', 'c': 'd', 'e': 'f'}
        properties = pika.BasicProperties(app_id='data_collect',
                                          content_type='application/json',
                                          delivery_mode=2,  # make message persistent
                                          headers=headers,
                                          )
        channel.basic_publish(exchange=exchange,
                              routing_key=routing_key,
                              body=json.dumps(message, ensure_ascii=False),
                              properties=properties,
                              )
    except Exception as exc:
        print(exc)
        return False
    return True


async def consume_items_from_rabbitmq(queue: asyncio.Queue, channel, queue_name: str, inactivity: int = 0.001):
    """
    Consumes items from a RabbitMQ Queue and puts the items onto an asyncio.Queue for consumption by a Service
    Runs forever.

    Args:
        queue: asyncio.Queue
        channel: pika.BlockingConnection().channel() object
        queue_name (str): name of a bound queue
        inactivity (int): timeout in s

    Returns:

    """

    while True:
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
                else:
                    # empty remaining items from queue
                    while queue.qsize():
                        await asyncio.sleep(ASYNC_SLEEP)
                    await asyncio.sleep(ASYNC_SLEEP)
        except Exception as exc:
            print(exc)

        requeued_messages = channel.cancel()


async def publish_items_to_rabbitmq(queue: asyncio.Queue, channel, exchange_name, routing_key: Optional[str] = None):
    """

    Do not supply routing key parameter if you are publishing to multiple queues. If so, then the message should be
    of the format:

    .. code-block:: python
        :linenos:

        msg = {'routing_key': routing.key,
               'body': {'keys': 'values'}
               }

    Args:
        queue:
        channel:
        exchange_name:
        routing_key:

    Returns:

    """

    while True:
        try:
            await asyncio.sleep(ASYNC_SLEEP)
            while not queue.empty():
            # if not queue.empty():
                msg = queue.get_nowait()
                # msg = await queue.get()
                if 'exit_routing_key' in msg and 'body' in msg and not routing_key:
                    publish_message_to_exchange(channel,
                                                exchange_name,
                                                routing_key=msg['exit_routing_key'],
                                                message=msg['body'])
                else:
                    publish_message_to_exchange(channel,
                                                exchange_name,
                                                routing_key=routing_key,
                                                message=msg)
                queue.task_done()
        except Exception as exc:
            print(exc.__repr__())

    connection.close()
