import pytest
from aiohttp.test_utils import ClientSession
from aiohttp import TCPConnector

from core.async_requests import AsyncHttpRequests


pytestmark = pytest.mark.asyncio


@pytest.fixture
def async_requests(request):
    return AsyncHttpRequests(**request.param)


@pytest.mark.parametrize('async_requests', [{'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': True,
                                             'use_headers': True
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': False,
                                             'use_headers': True
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': True,
                                             'use_headers': False
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': False,
                                             'use_headers': False
                                             },
                                            ], indirect=True)
@pytest.mark.parametrize('response_encoding,proxy_account', [(None, 'account_name'),
                                                             ('latin-1', 'account_name')])
async def test_make_request(async_requests, aresponses, response_encoding, proxy_account):
    async with ClientSession(connector=TCPConnector(limit=20, ssl=False)) as session:
        aresponses.add('google.com', '/asdf123', 'GET', response='OK')
        aresponses.add('foo.com', '/asdf123', 'GET', aresponses.Response(text='error', status=503), repeat=1)
# @pytest.mark.parametrize('async_requests', [{'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': True,
#                                              
#                                              'use_headers': True
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': False,
#                                              
#                                              'use_headers': True
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': True,
#                                              
#                                              'use_headers': False
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': False,
#                                              
#                                              'use_headers': False
#                                              }
#                                             ],
#                          indirect=True)
# @pytest.mark.parametrize('url', ['http://google.com/asdf123', 'https://foo.com/asdf123'])
# async def test_bulk_requests(async_requests, url, aresponses):
#     url_queue = [{'url': url, 'cache_url': None, 'retries': 0, 'response_encoding': None},
#                  {'url': url, 'cache_url': None, 'retries': 0, 'response_encoding': 'latin-1'},
#                  {'url': url, 'cache_url': 'http://google.com/asdf123', 'retries': 0, 'response_encoding': 'latin-1'},
#                  ]
#     # next_queue = async_queue.get_queue()
#     for next_queue in [async_queue.get_queue(), None]:
#         if url == 'https://foo.com/asdf123':
#             aresponses.add('foo.com', '/asdf123', 'GET', aresponses.Response(text='error', status=503), repeat=3+3+2)
#             aresponses.add('google.com', '/asdf123', 'GET', response='OK', repeat=1)
#         else:
#             aresponses.add('google.com', '/asdf123', 'GET', response='OK', repeat=3)
#
#         next_queue = await async_requests.bulk_requests(url_queue, next_queue)
#
#         ctr = 0
#         while next_queue.qsize():
#             item = await async_queue.get_from_queue(next_queue)
#             qitem = url_queue[ctr]
#             qitem['response'] = 'OK' if qitem['url'] == 'http://google.com/asdf123' or qitem['cache_url'] == \
#                                         'http://google.com/asdf123' else None
#             assert qitem == item
#             ctr += 1
#
#     aresponses.assert_all_requests_matched()#.assert_plan_strictly_followed()

        response, status_code = await async_requests.make_request(session, 'http://google.com/asdf123',
                                                                  proxy_account,
                                                                  response_encoding=response_encoding)
        assert response == 'OK'
        assert status_code == 200

        response, status_code = await async_requests.make_request(session, 'https://foo.com/asdf123',
                                                                  proxy_account,
                                                                  response_encoding=response_encoding)
        assert response == 'error'
        assert status_code == 503
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize('async_requests', [{'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': True,
                                             'use_headers': True
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': False,
                                             'use_headers': True
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': True,
                                             'use_headers': False
                                             },
                                            {'connections': 20,
                                             'retries': 3,
                                             'timeout': 100,
                                             'use_proxy': False,
                                             'use_headers': False
                                             }
                                            ],
                         indirect=True)
@pytest.mark.parametrize('url,proxy_account', [('http://google.com/asdf123', 'account_name'),
                                               ])
def test_prep_request_params(async_requests, url, proxy_account):
    header, proxy = async_requests.prep_request_params(url, proxy_account)
    if async_requests.use_headers:
        assert isinstance(header, dict)
        if async_requests.use_proxy:
            assert 'X-Crawlera-Profile' in header and 'User-Agent' not in header
        else:
            assert 'X-Crawlera-Profile' not in header and 'User-Agent' in header
    else:
        assert not header
    if async_requests.use_proxy:
        assert isinstance(proxy, str)
    else:
        assert not proxy


# @pytest.mark.parametrize('async_requests', [{'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': True,
#                                              'use_headers': True
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': False,
#                                              'use_headers': True
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': True,
#                                              'use_headers': False
#                                              },
#                                             {'connections': 2,
#                                              'retries': 3,
#                                              'timeout': 100,
#                                              'use_proxy': False,
#                                              'use_headers': False
#                                              }
#                                             ],
#                          indirect=True)
# @pytest.mark.parametrize('url', ['http://google.com/asdf123', 'https://foo.com/asdf123'])
# async def test_bulk_requests(async_requests, url, aresponses):
#     url_queue = [{'url': url, 'cache_url': None, 'retries': 0, 'response_encoding': None},
#                  {'url': url, 'cache_url': None, 'retries': 0, 'response_encoding': 'latin-1'},
#                  {'url': url, 'cache_url': 'http://google.com/asdf123', 'retries': 0, 'response_encoding': 'latin-1'},
#                  ]
#     # next_queue = async_queue.get_queue()
#     for next_queue in [async_queue.get_queue(), None]:
#         if url == 'https://foo.com/asdf123':
#             aresponses.add('foo.com', '/asdf123', 'GET', aresponses.Response(text='error', status=503), repeat=3+3+2)
#             aresponses.add('google.com', '/asdf123', 'GET', response='OK', repeat=1)
#         else:
#             aresponses.add('google.com', '/asdf123', 'GET', response='OK', repeat=3)
#
#         next_queue = await async_requests.bulk_requests(url_queue, next_queue)
#
#         ctr = 0
#         while next_queue.qsize():
#             item = await async_queue.get_from_queue(next_queue)
#             qitem = url_queue[ctr]
#             qitem['response'] = 'OK' if qitem['url'] == 'http://google.com/asdf123' or qitem['cache_url'] == \
#                                         'http://google.com/asdf123' else None
#             assert qitem == item
#             ctr += 1
#
#     aresponses.assert_all_requests_matched()#.assert_plan_strictly_followed()
