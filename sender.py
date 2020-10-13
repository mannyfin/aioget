"""Sends entities to the Search Service"""
import pika
import json

from configs.base.rabbit_connection import RABBIT_USER, RABBIT_PW, RABBITMQ_PORT

local = True
exchange_name = 'message'
search_routing_key = 'entity'
search_queue_name = 'search'

# while True:
credentials = pika.PlainCredentials(username=RABBIT_USER,
                                    password=RABBIT_PW,
                                    erase_on_connect=False)

if local:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=RABBITMQ_PORT, credentials=credentials))
else:
    # add your own remote IP address here to send messages between VMs
    remoteIP = 'remote IP address here'
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(remoteIP, RABBITMQ_PORT, '/', credentials, heartbeat=30, retry_delay=2), )

channel = connection.channel()
channel.exchange_declare(exchange='message', exchange_type='topic', durable=True)

routing_key = search_routing_key

queue = channel.queue_declare(search_queue_name, exclusive=False, durable=True, auto_delete=False)
channel.queue_bind(exchange=exchange_name, queue=search_queue_name, routing_key=routing_key)

_ = ['GOOGLE', 'APPLE']
for entity in _:
    channel.basic_publish(exchange='message',
                          routing_key=routing_key,
                          body=json.dumps({
                                           'client': 'default',
                                           'business_function': 'media',
                                           'language': 'en',
                                           'entity': entity
                                           }),
                          properties=pika.BasicProperties(delivery_mode=2)
                          )

connection.close()
