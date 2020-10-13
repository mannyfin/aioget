"""Example of receiving messages from RabbitMQ and saving the JSON to a file"""
import asyncio
import sys
import json

if sys.platform != 'win32':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from core import rabbitmq_router


async def consume_mult(queue, fpath):
    """fetches a record off the queue and saves to disk"""
    while True:
        if not queue.qsize():
            await asyncio.sleep(0.001)

        else:
            qitem = queue.get_nowait()
            try:
                jlqitem = json.loads(qitem)

                print('got', jlqitem)
                with open(fpath, 'a') as f:
                    f.write(f"{json.dumps(jlqitem)}\n")
            except Exception as exc:
                print(exc.__repr__())
                print('nope', qitem)

            queue.task_done()
        await asyncio.sleep(0.001)


async def consume_items_from_rabbitmq(queue):
    """fetches record from RabbitMQ and puts on a queue for processing."""
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
                    print(f'elapsed time: {end:.3f}\tmessages received: {ctr}')
            else:
                # empty remaining items from queue
                while queue.qsize():
                    await asyncio.sleep(0.001)
                end = time.time() - start
                print(f'elapsed time: {end:.3f}\tmessages received: {ctr}')
                break
            await asyncio.sleep(0.001)

        requeued_messages = channel.cancel()


async def main(records_path):
    await asyncio.gather(consume_items_from_rabbitmq(q), consume_mult(q, records_path))


if __name__ == "__main__":
    import time

    q = asyncio.Queue(maxsize=0)

    records_path = 'records.jsonl'
    exchange_name = 'message'
    post_parser_routing_key1 = '#.media'
    post_parser_routing_key2 = 'text'

    post_parser_queue_name = 'NEXT_SERVICE'
    queue_name = post_parser_queue_name
    routing_key1 = post_parser_routing_key1
    routing_key2 = post_parser_routing_key2

    connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', exchange_name=exchange_name,
                                                                      consumer=True,
                                                                      prefetch=5000)

    consume_queue = rabbitmq_router.create_queue(channel, queue_name)

    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key1)
    rabbitmq_router.bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key2)

    asyncio.run(main(records_path))
    channel.close()
    connection.close()
