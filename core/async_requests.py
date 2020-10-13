import asyncio
import aiohttp
from typing import Optional, Tuple

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from core.proxy import Proxy
from core import async_queue, logger

basiclogger = logger.rabbit_logger(__name__)


class AsyncHttpRequests(object):
    bot_resp = ["We've detected unusual activity from your computer network",
                'META NAME="ROBOTS"',
                ]

    def __init__(self, connections: int = 200,
                 retries: int = 3,
                 timeout: float = 100,
                 use_proxy: bool = True,
                 use_headers: bool = True, **kwargs):

        self.connections = connections
        self.retries = retries
        self.timeout = timeout
        # self.proxy = Proxy(use_proxy, proxy_account)
        self.use_proxy = use_proxy
        self.use_headers = use_headers
        if self.use_headers:
            self.ua = UserAgent()

    async def make_request(self, session: aiohttp.client.ClientSession,
                           url: str,
                           proxy_account: Optional[str] = None,
                           response_encoding: Optional[str] = None,
                           ssl: bool = False) -> Tuple[Optional[str], int]:
        """
        Make a single asynchronous request and return the response text and status code

        Args:
            proxy_account:
            session: An aiohttp.client.ClientSession object
            url: string
            response_encoding: encoding to apply for response text. Default None is utf-8
            ssl: ssl verification, Default. False

        Returns:
            response text (str), and response status code (int)
        """
        try:
            header, proxy = self.prep_request_params(url, proxy_account)

            async with session.get(url, ssl=ssl, timeout=self.timeout, headers=header, proxy=proxy) as resp:
                try:
                    response = await resp.text(encoding=response_encoding)
                    status_code = resp.status
                except UnicodeDecodeError:
                    response = await resp.read()
                    status_code = resp.status
                    soup = BeautifulSoup(response, 'lxml')
                    response = soup.__str__()
            return response, status_code
        except Exception as exc:
            basiclogger.error(exc.__repr__())
            return None, 600

    def prep_request_params(self, url: str, proxy_account: Optional[str] = None) -> Tuple[
        Optional[dict], Optional[str]]:
        """
        Creates the headers and proxy params for a request.
        Only creates headers if **self.use_headers = True** and
        only creates proxy if **self.use_proxy = True**.
        The aiohttp library as of this creation only supports http headers.

        Args:
            proxy_account:
            url: string

        Returns:
            header(dict), proxy(str)
        """
        if self.use_proxy:
            # aiohttp only supports http proxies
            proxy = Proxy(proxy_account)
            proxy_type = 'http'
            proxy = proxy.PROXIES[proxy_type]
        else:
            proxy = None

        if self.use_headers:
            # todo
            header = {'Accept-Encoding': 'gzip, deflate, br',
                      'X-Crawlera-Profile': 'desktop',
                      'X-Crawlera-Cookies': 'discard',
                      'Referer': '/'.join(url.split('/', 3)[:3]) + '/'
                      }
            if not self.use_proxy:
                header.pop('X-Crawlera-Profile')
                header.pop('X-Crawlera-Cookies')
                header['User-Agent'] = self.ua.random
            # header['X-Crawlera-Cookies'] = 'disable'
        else:
            header = None

        return header, proxy

    async def handle_requests(self, queue: asyncio.Queue, next_queue: asyncio.Queue, *args, **kwargs):
        """
        Called by the worker to make a single request and return a single response back to the worker.
        Tries a request up to self.retries number of times. If a cache_url is provided, it will attempt on the last
        attempt.

        Successful responses and failed responses are put onto the `next_queue` along with the item that was fetched
        from `queue`. Failed responses return None, and can be used for auditing purposes or retrying at a later date.

        Args:
            queue (asyncio.Queue): queue of dicts with at least the keys: url, cache_url, response_encoding.
            next_queue (asyncio.Queue): queue of dicts with at least the keys: url, cache_url, response_encoding,
            response.
            args:
            kwargs: includes the aiohttp.ClientSession object passed as session

        Returns:

        """
        try:
            item = await async_queue.get_from_queue(queue)
            response = None
            status_code = 600

            while status_code >= 400 and item['retries'] < self.retries:
                if item['retries'] == self.retries - 1 and item['cache_url']:
                    response, status_code = await self.make_request(session=kwargs['session'],
                                                                    url=item['cache_url'],
                                                                    proxy_account=item['proxy_account'],
                                                                    response_encoding=item['response_encoding'],
                                                                    )
                else:
                    response, status_code = await self.make_request(session=kwargs['session'],
                                                                    url=item['url'],
                                                                    proxy_account=item['proxy_account'],
                                                                    response_encoding=item['response_encoding'],
                                                                    )

                status_code = self.bot_response(status_code, response)
                # if response and "We've detected unusual activity from your computer network" in response:
                #     # bloomberg
                #     status_code = 700
                # elif response and 'META NAME="ROBOTS"' in response:
                #     # open corporates
                #     status_code = 700

                if status_code >= 400:
                    item['retries'] += 1

            item['response'] = response if status_code < 400 else None
            if item['response']:
                next_queue = await async_queue.set_onto_queue(next_queue, item)
            queue.task_done()
        except Exception as exc:
            basiclogger.error(exc.__repr__())
        # return next_queue

    def bot_response(self, status_code: int, response: str) -> int:
        """
        If response text has some typical bot stuff, count it as a fail with status_code 700. While those strings may
        occur in some tech or how-to articles, more likely than not we got banned.

        Args:
            status_code (int): status code of the response.
            response (str): response string

        Returns:
            status_code (int): The same status code if bot activity not detected, else 700 indicating a fail.
        """

        if response and any(k in response for k in self.bot_resp):
            # bloomberg
            status_code = 700
        return 700 if response and any(k in response for k in self.bot_resp) else status_code


    # async def bulk_requests(self, url_queue: list, next_queue: Optional[asyncio.Queue] = None) -> asyncio.Queue:
    #     """
    #     Pushes urls to be requested on a queue and has workers pop items off the queue and make requests.
    #     The workers return the item off the queue and the response, which are both pushed as a new item onto
    #     another queue object, **next_queue**.
    #
    #     Args:
    #         url_queue: List of dicts of {'url':url, 'cache_url':cache_url, 'retries': retries, kwargs)
    #         next_queue: asyncio.Queue object to push the response onto
    #
    #     Returns:
    #         next_queue with the completed {'url':url, 'cache_url':cache_url, 'retries': retries,
    #         'response': response, ... kwargs) dicts in FIFO.
    #     """
    #     queue = async_queue.get_queue()
    #     queue = await async_queue.set_many_onto_queue(queue, url_queue)
    #     if not next_queue:
    #         next_queue = async_queue.get_queue()
    #
    #     async with ClientSession(connector=TCPConnector(limit=self.connections, ssl=False)) as session:
    #         workers = []
    #         for _ in range(min(queue.qsize(), self.connections)):
    #             task = asyncio.create_task(async_queue.worker(queue, next_queue, self.handle_requests, session=session,
    #                                                           ))
    #             workers.append(task)
    #
    #         await asyncio.gather(*workers)
    #         await queue.join()
    #
    #         for consumer in workers:
    #             # canceling
    #             consumer.cancel()
    #         return next_queue
