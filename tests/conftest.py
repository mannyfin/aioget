import pytest

import logging

from _pytest import monkeypatch

from core import logger, rabbitmq_router
from configs.base.rabbit_connection import RABBITMQ_HOST, RABBITMQ_PORT, RABBIT_USER, RABBIT_PW

exchange_name = 'log'
connection, channel = rabbitmq_router.connect_to_message_exchange(host='localhost', exchange_name=exchange_name,
                                                                  consumer=True,
                                                                  prefetch=500)


@pytest.fixture(scope='session', autouse=True)
def basiclogger():
    host = RABBITMQ_HOST,
    port = RABBITMQ_PORT,
    connection_params = None
    formatter = logging.Formatter('%(asctime)s %(levelname)-6s [%(filename)-s: %(lineno)d] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M')

    # def assert_message(record):
    #     assert record.msg == message
    #     assert record.levelname == 'INFO'

    # mock a logging handler similar to the RabbitMQHandlerOneWay class
    class MockRabbitMQHandlerOneWay(logging.Handler):
        def __init__(self, host, port, formatter, connection_params, username, password, level=logging.DEBUG):
            self.host = host
            self.port = port
            self.connection_params = connection_params
            self.level = level
            super(MockRabbitMQHandlerOneWay, self).__init__(level=level)
            self.setFormatter(formatter)
            self.username = RABBIT_USER
            self.password = RABBIT_PW

        def emit(self, record):
            output = self.format(record)
            print(output)
            # assert_message(record)

    monkeypatch.MonkeyPatch().setattr('core.logger.RabbitMQHandlerOneWay', MockRabbitMQHandlerOneWay)

    basiclogger = logger.rabbit_logger(__name__)

    # example usage
    # basiclogger.info(message)
    return basiclogger
