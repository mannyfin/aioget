import pytest
import logging

from core import logger
from configs.base.rabbit_connection import RABBITMQ_HOST, RABBITMQ_PORT, RABBIT_USER, RABBIT_PW


@pytest.mark.parametrize('host, port, formatter, connection_params, message',
                         [(RABBITMQ_HOST,
                          RABBITMQ_PORT,
                          None,
                          logging.Formatter('%(asctime)s %(levelname)-6s [%(filename)-s: %(lineno)d] %(message)s',
                                            datefmt='%Y-%m-%d %H:%M'), 'hi'),
                          ])
def test_rabbit_logger(capsys, monkeypatch, host, port, formatter, connection_params, message):

    def assert_message(record):
        assert record.msg == message
        assert record.levelname == 'INFO'

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
            assert_message(record)

    monkeypatch.setattr('core.logger.RabbitMQHandlerOneWay', MockRabbitMQHandlerOneWay)

    basiclogger = logger.rabbit_logger(__name__)

    # example usage
    basiclogger.info(message)
