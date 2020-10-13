import os
import pytest
import asyncio

from download_svc.download import DownloadService
from configs.base.consts import PROJ_ROOT
from pytest_redis import factories

redis_external = factories.redisdb('redis_nooproc')

pytestmark = pytest.mark.asyncio


# @pytest.fixture()
# def queue():
#     """return instance of asyncio.Queue"""
#     return asyncio.Queue()

@pytest.fixture()
def download_service():
    in_queue, out_queue = asyncio.Queue(), asyncio.Queue()
    return DownloadService(input_queue=in_queue, publish_queue=out_queue)


async def test_start(aresponses, redis_external, basiclogger):
    url_queue = [
        {'url': 'https://www.example.org/',
                  'cache_url': '',
                  'retries': 0,
                  'language': 'en',
                  'entity': 'example',
                  'response_encoding': None},
                 {'url': 'https://example.org/',
                  'cache_url': '',
                  'retries': 0,
                  'language': 'en',
                  'entity': 'example',
                  'response_encoding': None},
                 {'url': 'https://failed.org/',
                  'cache_url': '',
                  'retries': 0,
                  'language': 'en',
                  'entity': 'example',
                  'response_encoding': None},
                 {'url': 'https://failed.org/',
                  'cache_url': 'https://cache_url_success.org/',
                  'retries': 0,
                  'language': 'en',
                  'entity': 'example',
                  'response_encoding': None},
                 {'url': 'https://missing_keys_catastrophic_fail.org/',
                  'cache_url': 'https://missing_keys_catastrophic_fail.org/',
                  'retries': 0,
                  'language': 'en',
                  'entity': 'example',
                  'response_encoding': None}
                 ]
    in_queue, out_queue = asyncio.Queue(), asyncio.Queue()
    download_service = DownloadService(input_queue=in_queue, publish_queue=out_queue)
    download_service.download_history = redis_external
    download_service.async_http_requests.connections = 5
    # in_queue, out_queue = asyncio.Queue(), asyncio.Queue()
    # download_service = DownloadService(input_queue=in_queue, publish_queue=out_queue)

    aresponses.add('www.example.org', '/', response='OK', method_pattern='GET')
    aresponses.add('example.org', '/', response='OK', method_pattern='GET')
    aresponses.add('failed.org', '/', 'GET', aresponses.Response(text='error', status=500), repeat=5)
    aresponses.add('cache_url_success.org', '/', response='OK', method_pattern='GET')

    for msg in url_queue:
        download_service.input_queue.put_nowait(msg)

    async def main(input_queue, output_queue, download_service):
        done, pending = 0, 0
        try:
            workers, queues, session = download_service.start()
            # await asyncio.sleep(0.1)
            done, pending = await asyncio.wait(workers, timeout=0.2)
            # for queue in queues:
            #     await queue.join()
            await input_queue.join()
            await output_queue.join()
            for consumer in workers:
                # canceling
                consumer.cancel()
            await session.close()

        except Exception as exc:
            print(exc.__repr__())
        return done, pending
    done, pending = await main(in_queue, out_queue, download_service)
    assert len(url_queue) == len([i for i in pending if 'write_response' in i._coro.__name__])


    # if isinstance(result, str):
    #     aresponses.assert_plan_strictly_followed()
    # else:
    #     assert not result and not os.path.isfile(download_service.dls_file_path)

# def test_write_response():
#     assert False
