import asyncio
import glob
import importlib
import json
import os
import time

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.utils import load_config, parse_consumer, make_config, set_arb, pop_arb_field_if_exists
from configs.base.consts import CONFIG_DIR, ASYNC_SLEEP
from core import logger, async_queue

from sys import platform
if platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

basiclogger = logger.rabbit_logger(__name__)


class ParserService(object):
    # BUSINESS_CONFIGS_DIR = f"{CONFIG_DIR}/business_drivers/search"  # NegMedia/SJA/LOB/etc
    CLIENT_CONFIGS_DIR = os.path.join(CONFIG_DIR, 'client')
    BUSINESS_CONFIGS_PATHS: str = os.path.join(CONFIG_DIR, 'business_drivers', 'parser', 'parser.json')
    CLIENT_CONFIGS_PATHS = glob.glob(os.path.join(CLIENT_CONFIGS_DIR, '*', '*.json'))

    def __init__(self, input_queue: asyncio.Queue, publish_queue: asyncio.Queue):

        self.business_configs = load_config(self.BUSINESS_CONFIGS_PATHS)
        self.client_configs = make_config(self.CLIENT_CONFIGS_PATHS)

        self.input_queue = input_queue
        self.publish_queue = publish_queue

        #  todo convert to push config
        self.config_refresh = time.time()
        self.import_parser_funcs()

    async def start(self):
        """
        Start the Download Service

        Returns:

        """
        try:
            # async_filesystem.create_fs(self.file_system_path)
            parse_queue = async_queue.get_queue()
            write_queue = async_queue.get_queue()

            workers = []
            for _ in range(100):  # range(self.async_http_requests.connections)):
                task = asyncio.create_task(self.put_onto_parse_queue(parse_queue))
                workers.append(task)

            task = asyncio.create_task(parse_consumer(next_queue=parse_queue, write_queue=write_queue
                                                      ))
            workers.append(task)

            task = asyncio.create_task(self.write_response(write_queue=write_queue,
                                                           ))
            workers.append(task)

            await asyncio.gather(*workers)
            await self.input_queue.join()
            await self.publish_queue.join()
            await parse_queue.join()
            await write_queue.join()

            for consumer in workers:
                # canceling
                consumer.cancel()

        except Exception as exc:
            # catastrophic failure...
            basiclogger.critical(exc.__repr__())

            return False

        return True

    def import_parser_funcs(self):
        """
        Dynamic importing of parse functions into the business configuration

        Examples:
            "media": "parser.snapshot.parse",

            will look for the `parse` function in the src/parser/snapshot.py module

            Then it will add the function to the service configuration under:
            service_config['funcs']['media'] = parse

            The parse func can be used normally:
            parse(kwargs)

        Returns:
            None
        """
        self.business_configs['funcs'] = {}
        for business_function, values in self.business_configs.items():
            try:
                if business_function == 'funcs':
                    continue
                modname, funcname = values['parser'].rsplit('.', 1)
                # mod = importlib.import_module(f'..{modname}', package=f'parser_scripts.{modname.split(".")[0]}')
                mod = importlib.import_module(modname)
                func = getattr(mod, funcname)
                self.business_configs['funcs'][business_function] = func
            except ModuleNotFoundError as exc:
                basiclogger.error(exc.__repr__())
            except Exception as exc:
                basiclogger.error(exc.__repr__())

    # def update_configs(self):
    #     # todo this should be outside the class
    #     # todo replace this with push notification
    #     now = time.time()
    #     # read in configs every hour
    #     if (now - self.config_refresh) / 3600 > 1:
    #         # Check if there are new configs
    #         # todo potential breakage if there are same outermost keys in the config files
    #         self.BUSINESS_CONFIGS_PATHS = glob.glob(os.path.join(self.BUSINESS_CONFIGS_DIR, '*.json'))
    #         self.CLIENT_CONFIGS_PATHS = glob.glob(os.path.join(self.CLIENT_CONFIGS_DIR, '*', '*.json'))
    #
    #         # self.service_configs = load_config(self.SEARCH_SERVICE_CONFIG_PATH)
    #         self.business_configs = make_config(self.BUSINESS_CONFIGS_PATHS)
    #         self.client_configs = make_config(self.CLIENT_CONFIGS_PATHS)
    #
    #         self.config_refresh = time.time()
    #         # todo, message to fanout exchange, logger.info('search service configs updated')
    #
    # def check_configs(self, business_function, client):
    #     if business_function not in self.business_configs or \
    #             client not in self.client_configs[business_function]:
    #         self.update_configs()
    #         if business_function not in self.business_configs:
    #             # todo for now default to negative media
    #             business_function = 'media'
    #         if client not in self.client_configs[business_function]:
    #             # todo for now default to 'default'
    #             client = 'default'
    #     return business_function, client
    #
    # def make_configuration(self, message):
    #     """
    #     Extract configuration for a specific search
    #
    #     Args:
    #         message (dict): JSON response message containing instructions on how to do a search
    #     Returns:
    #
    #     """
    #     # todo this should be outside the class?
    #     entity = message['entity']
    #     client = message['client'] if 'client' in message else ''
    #     business_function = message['business_function']
    #     # check that client/business function exist in the configs. If not update. If still not, then provide a default
    #     business_function, client = self.check_configs(business_function, client)
    #
    #     business_configuration = self.business_configs[business_function]
    #     client_search_configs = self.client_configs[business_function][client]
    #     return entity, business_configuration, client_search_configs

    async def put_onto_parse_queue(self, parse_queue: asyncio.Queue):
        """
        Read input messages, then add the appropriate parse func and then put onto parse_queue

        Args:
            parse_queue:

        Returns:

        """

        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            while self.input_queue.qsize():
                # if self.input_queue.qsize():
                message: dict = await self.input_queue.get()
                try:
                    if isinstance(message, bytes):
                        message = json.loads(message)

                    # include download_queue fields
                    if message['business_function'] in self.business_configs['funcs']:
                        # add func to parse the webpage.
                        message['parse_func'] = self.business_configs['funcs'][message['business_function']]
                        message['exit_routing_key'] = self.business_configs[message['business_function']][
                            'exit_routing_key']
                    else:
                        basiclogger.error(f"{message['business_function']} not found in parser_service_config")

                    if 'client' not in message:
                        message['client_config'] = {}
                    elif 'business_function' in message and message['business_function'] in self.client_configs and \
                            'client' in message and message['client'] in\
                            self.client_configs[message['business_function']]:
                        client_config = self.client_configs[message['business_function']][message['client']]
                        message['client_config'] = client_config
                    else:
                        basiclogger.error(f"{message['business_function']} or client: {message['client']} not found in "
                                          f"client_service_config")

                    #parser funcs expect an arb field if there are passthrough items
                    # arb, message = pop_arb_field_if_exists(message)
                    # message = set_arb(msg=message, arb=arb)

                    await parse_queue.put(message)
                    # print('parse_queue unfinished items', parse_queue._unfinished_tasks, flush=True)
                except Exception as exc:
                    basiclogger.error(exc.__repr__())

    async def write_response(self, write_queue: asyncio.Queue):

        # today = datetime.today().date().isoformat()
        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            futures = []
            for ctr in range(write_queue.qsize()):
                futures.append(write_queue.get_nowait())
                write_queue.task_done()
            while futures:
                for _ in asyncio.as_completed(futures):
                    try:
                        parsed_output = await _
                    except Exception as exc:
                        parsed_output = {}
                        basiclogger.critical(exc.__repr__())

                    try:
                        # result = await async_queue.get_from_queue(write_queue)
                        if parsed_output and self.publish_queue:

                            # print('parsed output', parsed_output, flush=True)
                            # only publish non empty result

                            routing_key = parsed_output.pop('exit_routing_key')
                            msg = {'exit_routing_key': routing_key,
                                   'body': parsed_output}
                            await self.publish_queue.put(msg)

                    except Exception as exc:
                        basiclogger.critical(exc.__repr__())

                if futures:
                    futures = [i for i in futures if not i.done()]


if __name__ == "__main__":
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    async def main(input_queue, output_queue):
        try:
            parser_service = ParserService(input_queue, output_queue)
            workers, queues, session = await parser_service.start()
            await asyncio.gather(*workers)
            for queue in queues:
                await queue.join()
            input_queue.join()
            output_queue.join()
            for consumer in workers:
                # canceling
                consumer.cancel()
            await session.close()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
    asyncio.run(main(input_queue, output_queue))