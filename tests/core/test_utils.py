import pytest
import os
from pathlib import Path
import json
import asyncio
from datetime import datetime
import pickle
# import pandas as pd

from core import utils
from parser_scripts import google
from search_svc.search import SearchService

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def config_path(request):
    cwd = Path(os.getcwd())
    if cwd.stem == 'tests':
        PATH = os.path.normpath('core/data/config.json')
    elif cwd.stem == 'core':
        PATH = os.path.normpath('data/config.json')
    else:
        raise ValueError(f'Current path is not right: {cwd.__str__()}')

    data = {1: 2, 'buckle_my': 'shoe'}
    with open(PATH, 'w') as f:
        json.dump(data, f)

    def teardown():
        os.remove(PATH)

    request.addfinalizer(teardown)
    return PATH


@pytest.fixture()
def model_path(request):
    cwd = Path(os.getcwd())
    if cwd.stem == 'tests':
        PATH = os.path.normpath('core/data/config.json')
    elif cwd.stem == 'core':
        PATH = os.path.normpath('data/config.json')
    else:
        raise ValueError(f'Current path is not right: {cwd.__str__()}')

    data = {1: 2, 'buckle_my': 'shoe'}
    with open(PATH, 'wb') as f:
        pickle.dump(data, f)

    def teardown():
        os.remove(PATH)

    request.addfinalizer(teardown)
    return PATH


@pytest.fixture(scope='module', params=[{'input_queue': asyncio.Queue,
                                         'publish_queue': asyncio.Queue, }])
def searchservice(request):
    return SearchService(**request.param)


def test_load_config(config_path):
    config = utils.load_config(config_path)
    assert isinstance(config, dict)


def test_load_model(model_path):
    model = utils.load_model(model_path)
    assert isinstance(model, dict)


# def test_date_range_maker():
#     assert False


def test_merge_configs():
    a = {1: 2, 3: 4}
    b = {3: 5, 5: 6}
    merged = utils.merge_configs(a, b)
    assert merged[3] == 5 and all(k in merged for k in (1, 3, 5))


# @pytest.mark.parametrize('fp, service',
#                          [('data/r1_google.json', 'google')])  # , ('data/r2_googlenews.json', 'googlenews')])
# async def test_process_pool(searchservice, fp, service):
#     today = datetime.today().date().isoformat()
#
#     # os.path.abspath(__file__)
#     filepath = os.path.normpath(os.path.join(os.path.split(os.getcwd())[0], f'service/{fp}'))
#     # with open(f"{PROJ_ROOT}/tests/service/{fp}", 'r') as f:
#     with open(filepath, 'r') as f:
#         qlist = json.load(f)
#
#     if service == 'google':
#         parse = google.parse
#         results = [{'entity': 'JOHN DOE',
#                     'date': today,
#                     'language': 'en',
#                     'urls': ['https://www.justice.gov/usao-ma/pr/john-doe-arrested-passport-fraud',
#                              'https://www.facebook.com/Kennewickpolice/posts/john-doe-arrested-today-officers-responded-to-a-local-business-for-a-male-loiter/2251568751576794/',
#                              'https://www.state.gov/john-doe-arrested-for-passport-fraud/',
#                              'https://www.tampabay.com/news/courts/in-jail-john-doe-inmates-often-identified/2188153/',
#                              'https://www.kbzk.com/news/local-news/john-doe-arrested-after-threatening-bozeman-bar-employees-with-bow-and-arrow',
#                              'https://thisweekinworcester.com/southbridge-john-doe-arrested/',
#                              'https://www.cnn.com/2007/US/law/12/10/court.indicting.dna/index.html',
#                              'https://www.ice.gov/news/releases/update-ice-arrests-john-doe-child-pornography-suspect-rescues-child-ongoing-sexual',
#                              'https://www.smdp.com/john-doe-gets-arrested-and-identified/157179'],
#                     'cache_urls': [
#                         'https://webcache.googleusercontent.com/search?q=cache:jdKcIjR4p6AJ:https://www.justice.gov/usao-ma/pr/john-doe-arrested-passport-fraud+&cd=1&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:n8A_JO5guCAJ:https://www.facebook.com/Kennewickpolice/posts/john-doe-arrested-today-officers-responded-to-a-local-business-for-a-male-loiter/2251568751576794/+&cd=2&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:jOtVmHGtnAQJ:https://www.state.gov/john-doe-arrested-for-passport-fraud/+&cd=3&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:dhQvzz5OAY8J:https://www.tampabay.com/news/courts/in-jail-john-doe-inmates-often-identified/2188153/+&cd=4&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:RmBlSGYAzzMJ:https://www.kbzk.com/news/local-news/john-doe-arrested-after-threatening-bozeman-bar-employees-with-bow-and-arrow+&cd=5&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:4r9NmF6ciP4J:https://thisweekinworcester.com/southbridge-john-doe-arrested/+&cd=6&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:DbUbgnKy2IwJ:https://www.cnn.com/2007/US/law/12/10/court.indicting.dna/index.html+&cd=7&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:DbvPF-EquQwJ:https://www.ice.gov/news/releases/update-ice-arrests-john-doe-child-pornography-suspect-rescues-child-ongoing-sexual+&cd=8&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:Qleb8-vJgagJ:https://www.smdp.com/john-doe-gets-arrested-and-identified/157179+&cd=9&hl=en&ct=clnk&gl=us'],
#                     'search_url': 'https://www.google.com/search?safe=strict&q=%22JOHN+DOE%22+AND+%28%22arrested%22'
#                                   '+OR+%22money+laundering%22%29+',
#                     'error': '',
#
#                     },
#                    {'entity': 'JANE DOE', 'date': today, 'language': 'en', 'urls': [
#                        'https://www.wsaw.com/content/news/Wisconsin-authorities-1999-slaying-victim-IDed-arrest-made-564653351.html',
#                        'https://cowboystatedaily.com/2020/05/07/iowa-man-arrested-in-wyoming-bitter-creek-betty-i-90-jane-doe-murder-cases/',
#                        'https://thesheridanpress.com/125244/alleged-jane-doe-killer-to-be-tried-in-tennessee-first/',
#                        'https://www.kenoshanews.com/news/local/jane-doe-identified-woman-arrested-for-years-of-abuse/article_259c079d-1b0d-5b22-8176-5c1ffe07c4a2.html',
#                        'https://www.wbal.com/article/419940/3/woman-arrested-for-1999-murder-of-jane-doe-found-in-cornfield-victim-suffered-barbaric-brutality-sheriff-says',
#                        'https://en.wikipedia.org/wiki/Long_Beach_Jane_Doe',
#                        'https://en.wikipedia.org/wiki/Long_Beach_Jane_Doe+%22JANE+DOE%22+AND+(%22arrested%22+OR+%22money+laundering%22)&tbo=1&sa=X&ved=2ahUKEwjuq4HPrIfqAhUzguYKHVomC-IQHzAFegQIAhAH',
#                        'https://en.wikipedia.org/wiki/Strangling',
#                        'https://en.wikipedia.org/wiki/Long_Beach,_California',
#                        'https://abcnews.go.com/US/woman-arrested-1999-murder-jane-doe-found-cornfield/story?id=66849268',
#                        'https://www.justice.gov/usao-cdca/pr/tips-members-public-lead-arrest-woman-charged-jane-doe-federal-child-pornography',
#                        'https://www.nydailynews.com/news/national/ny-arrest-wisconsin-jane-doe-murder-case-20191110-ao524lxqofgv7la52v3olsykpq-story.html'],
#                     'cache_urls': [
#                         'https://webcache.googleusercontent.com/search?q=cache:M2Tqm30RcpAJ:https://www.wsaw.com/content/news/Wisconsin-authorities-1999-slaying-victim-IDed-arrest-made-564653351.html+&cd=1&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:TeCzOGk5RA0J:https://cowboystatedaily.com/2020/05/07/iowa-man-arrested-in-wyoming-bitter-creek-betty-i-90-jane-doe-murder-cases/+&cd=2&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:BSTYfq9y_ckJ:https://thesheridanpress.com/125244/alleged-jane-doe-killer-to-be-tried-in-tennessee-first/+&cd=3&hl=en&ct=clnk&gl=us',
#                         '',
#                         'https://webcache.googleusercontent.com/search?q=cache:UikNVB_wzSUJ:https://www.wbal.com/article/419940/3/woman-arrested-for-1999-murder-of-jane-doe-found-in-cornfield-victim-suffered-barbaric-brutality-sheriff-says+&cd=5&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:VZRRS-8buvMJ:https://en.wikipedia.org/wiki/Long_Beach_Jane_Doe+&cd=6&hl=en&ct=clnk&gl=us',
#                         '', '', '',
#                         'https://webcache.googleusercontent.com/search?q=cache:xuK-H7uoZ_oJ:https://abcnews.go.com/US/woman-arrested-1999-murder-jane-doe-found-cornfield/story%3Fid%3D66849268+&cd=7&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:917jlAgQQBMJ:https://www.justice.gov/usao-cdca/pr/tips-members-public-lead-arrest-woman-charged-jane-doe-federal-child-pornography+&cd=8&hl=en&ct=clnk&gl=us',
#                         'https://webcache.googleusercontent.com/search?q=cache:YgIEL7H85oUJ:https://www.nydailynews.com/news/national/ny-arrest-wisconsin-jane-doe-murder-case-20191110-ao524lxqofgv7la52v3olsykpq-story.html+&cd=9&hl=en&ct=clnk&gl=us'],
#                     'search_url': 'https://www.google.com/search?safe=strict&q=%22JANE+DOE%22+AND+%28%22arrested%22+OR+%22money+laundering%22%29+',
#                     'error': ''},
#                    ]
#     # else:
#     #     results = [{'error': '', 'parsed_output': i} for i in [{'entity': 'JANE DOE', 'date': today, 'langugage': 'es',
#     #                                                             'client': '', 'business_function':'',
#     #                                                             'https://news.google.com/search?q=%22JANE+DOE%22+%22arrested%22++%20-excluded&hl=es-419&gl=US'
#     #                                                             '&ceid=US:es-419'],
#     #                                                            ['JOHN DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JOHN+DOE%22+%22money+laundering%22+%20'
#     #                                                             '-excluded&hl=es-419&gl=US&ceid=US:es-419'],
#     #                                                            ['JOHN DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JOHN+DOE%22+%22arrested%22+site%3Aexample.com+%20-excluded'
#     #                                                             '&hl=es-419&gl=US&ceid=US:es-419+'],
#     #                                                            ['JOHN DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JOHN+DOE%22+%22arrested%22++%20-excluded&hl=es-419&gl=US'
#     #                                                             '&ceid=US:es-419'],
#     #                                                            ['JANE DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JANE+DOE%22+%22money+laundering%22+%20'
#     #                                                             '-excluded&hl=es-419&gl=US&ceid=US:es-419'],
#     #                                                            ['JANE DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JANE+DOE%22+%22arrested%22+site%3Aexample.com+%20-excluded'
#     #                                                             '&hl=es-419&gl=US&ceid=US:es-419+'],
#     #                                                            ['JOHN DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JOHN+DOE%22+%22money+laundering%22+site'
#     #                                                             '%3Aexample.com%20-excluded&hl=es-419&gl=US&ceid=US:es-419+'],
#     #                                                            ['JANE DOE', today, 'es', '', '',
#     #                                                             'https://news.google.com/search?q=%22JANE+DOE%22+%22money+laundering%22+site'
#     #                                                             '%3Aexample.com%20-excluded&hl=es-419&gl=US&ceid=US:es-419+'],
#     #                                                            ]
#     #                ]
#     #     parse = googlenews.parse
#
#     futures = utils.process_pool(workers=0, func=parse, iterable=qlist)
#     for _ in asyncio.as_completed(futures):
#         parsed_output = await _
#         assert parsed_output in results
#         # print(parsed_output)
#
#     queue = asyncio.Queue()
#     for qitem in qlist:
#         queue.put_nowait(qitem)
#
#     futures = utils.process_pool(workers=0, func=parse, iterable=queue)
#     for _ in asyncio.as_completed(futures):
#         parsed_output = await _
#         assert parsed_output in results


@pytest.mark.parametrize('msg', [{'entity': 'TEST',
                                  'business_function': 'media',
                                  'client': 'default',
                                  'parse_func': lambda x: repr(x),
                                  'arb': {'success': 1}
                                  },
                                 {'entity': 'TEST',
                                  'business_function': 'media',
                                  'client': 'default',
                                  'parse_func': lambda x: repr(x),
                                  },
                                 ])
def test_pop_arb_field_if_exists(msg):
    msglen = len(msg)
    if 'arb' in msg:
        arb, msg = utils.pop_arb_field_if_exists(msg)
        assert arb and len(arb) == 1 and 'arb' not in msg
    else:
        arb, msg = utils.pop_arb_field_if_exists(msg)
        assert not arb
    assert len(msg) == msglen - len(arb)


@pytest.mark.parametrize('msg, arb', [({'entity': 'TEST',
                                        'business_function': 'media',
                                        'client': 'default',
                                        'parse_func': lambda x: repr(x)},
                                       {'success': 1}),
                                      ({'entity': 'TEST',
                                        'business_function': 'media',
                                        'client': 'default',
                                        'parse_func': lambda x: repr(x)},
                                       {}),
                                      ])
def test_set_arb(msg, arb):
    msglen = len(msg)
    assert msglen + len(arb) == len(utils.set_arb(msg, arb))
    assert 'arb' in msg if arb else 'arb' not in msg
