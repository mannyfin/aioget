import logging
from typing import Optional
import socket

from python_logging_rabbitmq import RabbitMQHandlerOneWay
import pika

from configs.base.rabbit_connection import RABBITMQ_HOST, RABBITMQ_PORT, RABBIT_USER, RABBIT_PW
# from core import rabbitmq_router


# exchange_name = 'log'
# connection, channel = rabbitmq_router.connect_to_message_exchange(host=RABBITMQ_HOST, exchange_name=exchange_name,
#                                                                   consumer=True,
#                                                                   prefetch=500)


def rabbit_logger(name: str, level='debug', host=RABBITMQ_HOST, port=RABBITMQ_PORT,
                  connection_params: Optional[pika.ConnectionParameters] = None,
                  format_log: bool = True):
    # try:
    #     socket.gethostbyname(RABBITMQ_HOST)
    # except socket.gaierror:
    #     host = 'localhost'

    logger = logging.getLogger(name)

    level = level.lower()
    if level == 'critical':
        logger.setLevel(logging.CRITICAL)
        logger.setLevel(logging.DEBUG)
    elif level == 'info':
        logger.setLevel(logging.INFO)
    elif level == 'warning':
        logger.setLevel(logging.WARNING)
    elif level == 'error':
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.DEBUG)
    if format_log:
        # by default RabbitMQHandler uses a JSON formatter, but we'll use a string.
        formatter = logging.Formatter('%(asctime)s %(levelname)-6s [%(filename)-s: %(lineno)d] %(message)s',
                                      datefmt='%Y-%m-%d %H:%M')
    else:
        formatter = None

    rabbit = RabbitMQHandlerOneWay(host=host, port=port, formatter=formatter,
                                   username=RABBIT_USER, password=RABBIT_PW,
                                   connection_params=connection_params)
    logger.addHandler(rabbit)
    logger.propagate = False
    return logger

