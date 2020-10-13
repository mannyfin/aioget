import asyncio
import json
from datetime import datetime
from typing import Optional
import os
import re
import importlib
from urllib.request import url2pathname
from pathlib import Path

from aiohttp.client import ClientSession, TCPConnector
import redis

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from configs.base.consts import CONFIG_DIR, ASYNC_SLEEP, PROJ_ROOT
from core import logger, async_queue, filtration, async_filesystem
from core.async_requests import AsyncHttpRequests
from core.utils import load_config, pop_arb_field_if_exists, set_arb

basiclogger = logger.rabbit_logger(__name__)


class DownloadService(object):
    SVC_CONFIG_PATH: str = os.path.join(CONFIG_DIR, 'service', 'download.json')
    BIZ_CONFIG_PATH: str = os.path.join(CONFIG_DIR, 'business_drivers', 'download', 'download.json')

    def __init__(self, input_queue: asyncio.Queue, publish_queue: asyncio.Queue):
        self.service_config = load_config(self.SVC_CONFIG_PATH)
        self.business_config = load_config(self.BIZ_CONFIG_PATH)

        self.import_parser_funcs()

        self.input_queue = input_queue
        self.publish_queue = publish_queue

        self.file_system_path = os.path.join(PROJ_ROOT, 'webpages')
        self.file_system_path_pathlib = Path(self.file_system_path)
        self.async_http_requests = AsyncHttpRequests(**self.service_config)

        ############################
        # self.service_config['redis_db_params']['host'] = 'localhost'

        self.download_history = redis.Redis(**self.service_config['redis_db_params'])

        self.total = 0
        # self.timeit = time.time()

    def start(self):
        """
        Start the Download Service

        Returns:

        ..todo: in filtering downloads, if download already exists, but for different business function, just bypass
        downloads
        """
        # try:
        async_filesystem.create_fs(self.file_system_path)
        download_queue = async_queue.get_queue(maxsize=200)
        write_queue = async_queue.get_queue()

        # async with ClientSession(connector=TCPConnector(limit=self.async_http_requests.connections, ssl=False)) as \
        #         session:
        session = ClientSession(connector=TCPConnector(limit=self.async_http_requests.connections, ssl=False))
        workers = []
        for _ in range(self.async_http_requests.connections):  # range(self.async_http_requests.connections):
            task = asyncio.create_task(self.put_onto_download_queue(download_queue))
            workers.append(task)
            task = asyncio.create_task(async_queue.worker(download_queue, write_queue,
                                                          self.async_http_requests.handle_requests,
                                                          session=session,
                                                          ))
            workers.append(task)

            task = asyncio.create_task(self.write_response(write_queue=write_queue,
                                                           publish_queue=self.publish_queue))
            workers.append(task)

        queues = [self.input_queue, self.publish_queue, download_queue, write_queue]
        return workers, queues, session

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
        self.business_config['funcs'] = {}
        for business_function, values in self.business_config.items():
            try:
                if business_function == 'funcs':
                    continue
                modname, funcname = values['url_fixer'].rsplit('.', 1)
                # mod = importlib.import_module(f'..{modname}', package=f'parser_scripts.{modname.split(".")[0]}')
                mod = importlib.import_module(modname)
                func = getattr(mod, funcname)
                self.business_config['funcs'][business_function] = func
            except ModuleNotFoundError as exc:
                basiclogger.error(exc.__repr__())
            except Exception as exc:
                basiclogger.error(exc.__repr__())

    async def put_onto_download_queue(self, download_queue: asyncio.Queue):

        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            while self.input_queue.qsize():
                if download_queue.full():
                    await asyncio.sleep(ASYNC_SLEEP)
                    continue
                try:
                    message: dict = self.input_queue.get_nowait()
                    if isinstance(message, bytes):
                        message = json.loads(message)

                    # use a preferred url to get results in english, remove google translate, etc.
                    if 'business_function' in message and message['business_function'] in self.business_config['funcs']:
                        message['url'] = self.business_config['funcs'][message['business_function']](message['url'])
                        if not message['url']:
                            # don't even bother fetching it.
                            self.input_queue.task_done()
                            continue

                    # check fixed url in Redis
                    keep_url = filtration.filter_already_downloaded_url_redis(message['url'],
                                                                              self.service_config['refresh_period'],
                                                                              self.download_history)
                    keep_cache_url = True
                    if 'cache_url' in message and message['cache_url']:
                        keep_cache_url = filtration.filter_already_downloaded_url_redis(message['cache_url'],
                                                                                        self.service_config['refresh_period'],
                                                                                        self.download_history)
                    if keep_url and keep_cache_url:
                        # include download_queue fields
                        message['retries'] = 0
                        message['proxy_account'] = self.service_config['proxy_account']
                        message['response_encoding'] = None

                        # await download_queue.put(message)
                        download_queue.put_nowait(message)
                    else:
                        if 'cache_url' in message:
                            basiclogger.info(f"duplicate url: {message['url']}\t{message['cache_url']}")
                        else:
                            basiclogger.info(f"duplicate url: {message['url']}")

                    if download_queue._unfinished_tasks and not download_queue._unfinished_tasks % 10:
                        basiclogger.debug(f'download queue unfinished items: {download_queue._unfinished_tasks}')
                    self.input_queue.task_done()
                except Exception as exc:
                    basiclogger.error(exc.__repr__())

    async def write_response(self, write_queue: asyncio.Queue, publish_queue: Optional[asyncio.Queue]):
        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            while write_queue.qsize():
                try:
                    today = datetime.today().date().isoformat()

                    encoded_url = ''
                    success = 0
                    # result = await async_queue.get_from_queue(write_queue)
                    result = write_queue.get_nowait()
                    if 'cache_url' in result and result['cache_url'] and result['retries'] >= \
                            self.async_http_requests.retries - 1:
                        url = result['cache_url']
                    else:
                        url = result['url']

                    if result['response']:
                        # todo need to check if encoding is present in the result
                        fpath: Path = self.file_system_path_pathlib.joinpath(*Path(url2pathname(url).split(':', 1)[-1]).parts[1:])
                        dirpath: Path = fpath.parent
                        dirpath.mkdir(parents=True, exist_ok=True)
                        encoded_url = await async_filesystem.save_file(fpath.__str__(),
                                                                       result['response'],
                                                                       encoding=result['response_encoding'])
                        if encoded_url:
                            # If there's some failure in saving the file...then success == 0
                            success = 1

                    # todo analyze tradeoff between sending the full response in a rabbitmq msg over network vs
                    #  i/o saving/reading from disk (also possibly over cloud storage)
                    _1 = result.pop('response') if 'response' in result else ''
                    _2 = result.pop('response_encoding') if 'response_encoding' in result else ''

                    result['encoded_url'] = encoded_url
                    msg = result

                    # rm arb messages before adding to download history
                    arb, msg = pop_arb_field_if_exists(msg)

                    if publish_queue and success:
                        # publish message
                        publish_queue.put_nowait(set_arb(msg=msg, arb=arb))

                    # needed for the filtration.filter_already_downloaded_url_redis function
                    msg['date'] = today
                    msg['success'] = success

                    self.download_history.set(url, json.dumps(msg))
                    write_queue.task_done()
                    self.total += 1
                    if not self.total % 10:
                        # elapsed = time.time() - self.timeit
                        basiclogger.debug(f'total completed: {self.total}')

                except Exception as exc:
                    basiclogger.critical(exc.__repr__())


if __name__ == "__main__":
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    async def main(input_queue, output_queue):
        try:
            download_service = DownloadService(input_queue, output_queue)
            workers, queues, session = await download_service.start()
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