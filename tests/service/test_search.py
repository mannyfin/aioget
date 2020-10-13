import pytest
import asyncio
from datetime import datetime

from search_svc.search import SearchService
from tests.conftest import basiclogger

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def entities():
    return ['JOHN DOE', 'JANE DOE']


@pytest.fixture()
def keywords():
    return ['arrested', 'convicted']


# @pytest.fixture
# def service_options():
#     return {"google": {"en": {"start_url": "https://www.google.com/search?safe=strict&q=",
#                               "host_lang": ""
#                               },
#                        "es": {"start_url": "https://www.google.es/search?safe=strict&q=",
#                               "host_lang": "&hl=es-419&gl=US&ceid=US:es-419"
#                               },
#                        "spain": {"start_url": "https://www.google.es/search?safe=strict&q=",
#                                  "host_lang": "&lr=lang_es&hl=es&gl=ES&cr=countryES"
#                                  }
#                        },
#             "googlenews": {"en": {"start_url": "https://news.google.com/search?q=",
#                                   "host_lang": ""
#                                   },
#                            "es": {"start_url": "https://news.google.com/search?q=",
#                                   "host_lang": "&hl=es-419&gl=US&ceid=US:es-419"
#                                   }
#                            }
#             }


# 'service, output_path, entities, keywords, language, websites, proxy_account, or_combine_kw, '
#                          'keywords_excluded, date_range'


@pytest.fixture(scope='module',
                params=[{'input_queue': asyncio.Queue(),
                         'publish_queue': asyncio.Queue()},
                        ])
def searchservice(request):
    return SearchService(**request.param)


@pytest.mark.parametrize('message, url',
                         [({
                               "entity": 'entity',
                               "client": 'default',
                               "business_function": "media"
                           },
                           "https://news.google.com/search?q=%22entity%22+AND+%28%22money+laundering%22+OR+%22ponzi"
                           "+scheme%22+OR+%22smuggling%22 "
                           "+OR+%22tax+evasion%22+OR+%22terrorism%22+OR+%22trafficking%22+OR+%22bribery%22+OR"
                           "+%22convicted%22+OR+%22corruption "
                           "%22+OR+%22embezzlement%22+OR+%22narcotic%22+OR+%22arrested%22+OR+%22fraud%22+OR"
                           "+%22indicted%22+OR+%22indictment%22 "
                           "+OR+%22jailed%22+OR+%22lawsuit%22%29+ "
                         ),
                             # {
                             #     "entity": 'entity',
                             #     "client": 'default',
                             #     "business_function": "line_of_business"
                             # },
                             # {
                             #     "entity": 'entity',
                             #     "client": 'default',
                             #     "business_function": "sja"
                             # },
                         ])
async def test_start(searchservice, message, url):
    # sinaloa_url = r'/search?safe=strict&q=%22SINALOA%22+AND+%28%22arrested%22+OR+%22money' \
    #               '+laundering%22%29+ '
    # pablo_escobar_url = r'/search?safe=strict&q=%22PABLO+ESCOBAR%22+AND+%28%22arrested%22+OR' \
    #                     '+%22money+laundering%22%29+ '
    # el_chapo_url = r'/search?safe=strict&q=%22EL+CHAPO%22+AND+%28%22arrested%22+OR+%22money' \
    #                '+laundering%22%29+ '
    #
    # with open(f"{PROJ_ROOT}/tests/service/data/sinaloa_google.html", 'r') as f:
    #     sinaloa = f.read()
    # with open(f"{PROJ_ROOT}/tests/service/data/pablo_escobar_google.html", 'r') as f:
    #     escobar = f.read()
    # with open(f"{PROJ_ROOT}/tests/service/data/el_chapo_google.html", 'r') as f:
    #     elchapo = f.read()
    # import re
    # aresponses.add(re.compile(r".*\.?google\.com"), sinaloa_url, method_pattern='GET',
    #                response=aresponses.Response(text=sinaloa, status=200), repeat=math.inf)
    # aresponses.add(re.compile(r".*\.?google\.com"), pablo_escobar_url, method_pattern='GET',
    #                response=aresponses.Response(text=escobar, status=200), repeat=math.inf)
    # aresponses.add(re.compile(r".*\.?google\.com"), el_chapo_url, method_pattern='GET',
    #                response=aresponses.Response(text=elchapo, status=200), repeat=math.inf)

    # ents = searchservice.entities
    # searchservice.entities = ['PABLO ESCOBAR', 'EL CHAPO', 'SINALOA'] * 5
    # searchservice.service = 'google'
    # todo figure out why new edge case is found...
    # aresponses.add(url, method_pattern='GET',
    #                response=aresponses.Response(text="1,2,3,4,5", status=200), repeat=1)
    searchservice.input_queue.put_nowait(message)
    workers, queues, session = searchservice.start()
    # searchservice.entities = ents
    # aresponses.assert_all_requests_matched()


@pytest.mark.parametrize('business_configuration', [{'lob_root': 'root/path',
                                                     'service': 'google',
                                                     'or_combine_kw': False,
                                                     'proxy_account': 'account_name',
                                                     'refresh_period': {'days': 0, 'months': 6, 'years': 0},
                                                     'keywords': {'en': ['', 'company profile']},
                                                     'keywords_excluded': {'en': []},
                                                     'url_filter_exclusion_patterns': ['facebook.com',
                                                                                       'linkedin.com',
                                                                                       'twitter.com',
                                                                                       'instagram.com',
                                                                                       'www.glassdoor.',
                                                                                       'www.indeed.',
                                                                                       'www.britannica.com',
                                                                                       'myspace',
                                                                                       'youtube.com',
                                                                                       'wikipedia',
                                                                                       'pinterest',
                                                                                       'reddit',
                                                                                       'amazon.com',
                                                                                       'alibaba.com',
                                                                                       'github.com',
                                                                                       'dictionary.',
                                                                                       'wiktionary.org',
                                                                                       'www.linguee.',
                                                                                       'yelp.com',
                                                                                       'www.tripadvisor',
                                                                                       'soundcloud.com',
                                                                                       'www.gettyimages.',
                                                                                       'groupdating.club',
                                                                                       'www.ancestry.com',
                                                                                       'https://translate.google.com',
                                                                                       'www.ziprecruiter.com',
                                                                                       '200.88.114.33',
                                                                                       'merriam-webster.com',
                                                                                       'spotify.com',
                                                                                       'prezi.com',
                                                                                       'classroom.google.com',
                                                                                       'www.espn.com',
                                                                                       'www.geeksforgeeks.org',
                                                                                       'www.quora.com',
                                                                                       'support.google.com',
                                                                                       'www.airbnb.',
                                                                                       'www.expedia.',
                                                                                       'www.tutorialspoint.com',
                                                                                       'moovitapp.com',
                                                                                       'mapquest.com',
                                                                                       'www.opentable.com',
                                                                                       'outlook.live.com',
                                                                                       'www.carinsuranceguidebook.',
                                                                                       '419scam.org',
                                                                                       'www.abercrombie.',
                                                                                       'www.helpwanted.',
                                                                                       'pornhub',
                                                                                       'xnxx',
                                                                                       'playboy',
                                                                                       'xvideos.com',
                                                                                       'torrent',
                                                                                       'porno',
                                                                                       'play.google.com',
                                                                                       'films',
                                                                                       'movies',
                                                                                       'boob',
                                                                                       'xporn',
                                                                                       'dirtyporn',
                                                                                       '\\.tk',
                                                                                       'imgur.com',
                                                                                       'www.waitrose.com',
                                                                                       'twitch.tv',
                                                                                       'celllookups.com',
                                                                                       'www.researchgate.net',
                                                                                       'www.mlb.com',
                                                                                       'rstudio.com',
                                                                                       'tumblr.com',
                                                                                       '\\.gz',
                                                                                       'https://scholar.google.com/citations?',
                                                                                       'www.dreamville.com/',
                                                                                       'www.learn-c.org',
                                                                                       'www.kaggle.com',
                                                                                       'www.cprogramming.com',
                                                                                       'www.jcrew.com',
                                                                                       'r-project.org',
                                                                                       'www.apartments.com',
                                                                                       'www.imdb.com',
                                                                                       'science.sciencemag.org/content',
                                                                                       'krecs.com',
                                                                                       'https://qz.com/1302211/haitch-or-aitch-english-speakers-cant-agree-on-how-to-say-h/',
                                                                                       'http://dev.stein.cl/sli/apertura/FormDapi.aspx?User=CTAMAYO&IdEjec=CTS',
                                                                                       'www.shutterstock.com',
                                                                                       'https://books.google.com',
                                                                                       'quizlet.com',
                                                                                       'gsuite.google.com',
                                                                                       'www.vocabulary.com',
                                                                                       'https://sites.google.com/site/hj7cbm27/ConsumerElectronics/etraders',
                                                                                       '\\.xls',
                                                                                       '\\.xlsx',
                                                                                       '\\.pdf',
                                                                                       '\\.doc',
                                                                                       '\\.docx',
                                                                                       '\\.jpg',
                                                                                       '\\.ppsx',
                                                                                       '\\.jpeg',
                                                                                       '\\.mp4',
                                                                                       '\\.mp3',
                                                                                       'ftp://'],
                                                     'websites': ['bloomberg.com/profile/company',
                                                                  'reuters.com/companies/',
                                                                  'emis.com/php/company-profile']}])
def test__get_start_url_host_lang(searchservice, business_configuration):
    for language in business_configuration['keywords'].keys():
        start_url, host_lang = searchservice._get_start_url_host_lang(language, business_configuration)
        assert searchservice.service_configs['service_option'][business_configuration['service']][language][
                   'start_url'] == start_url
        assert searchservice.service_configs['service_option'][business_configuration['service']][language][
                   'host_lang'] == host_lang


@pytest.mark.parametrize('message', [{
    "entity": 'entity',
    "client": 'default',
    "business_function": "media"
},
    {
        "entity": 'entity',
        "client": 'default',
        "business_function": "line_of_business"
    },
    {
        "entity": 'entity',
        "client": 'default',
        "business_function": "sja"
    },
])
def test_make_configuration(searchservice, message):
    entity, business_configuration, client_search_configs = searchservice.make_configuration(message)
    assert entity == message['entity']
    assert business_configuration == searchservice.business_configs['search'][message['business_function']]
    assert client_search_configs == searchservice.client_configs[message['business_function']][message['client']]


@pytest.mark.parametrize('entity,business_configuration,client_search_configs',
                         [
                             ('entity', {'lob_root': 'root/path',
                                         'service': 'google',
                                         'or_combine_kw': False,
                                         'or_combine_websites': True,
                                         'proxy_account': 'account_name',
                                         'refresh_period': {'days': 0, 'months': 6, 'years': 0},
                                         'keywords': {'en': ['', 'company profile']},
                                         'keywords_excluded': {'en': []},
                                         'url_filter_exclusion_patterns': ['facebook.com',
                                                                           'linkedin.com',
                                                                           'twitter.com',
                                                                           'instagram.com',
                                                                           'www.glassdoor.',
                                                                           'www.indeed.',
                                                                           'www.britannica.com',
                                                                           'myspace',
                                                                           'youtube.com',
                                                                           'wikipedia',
                                                                           'pinterest',
                                                                           'reddit',
                                                                           'amazon.com',
                                                                           'alibaba.com',
                                                                           'github.com',
                                                                           'dictionary.',
                                                                           'wiktionary.org',
                                                                           'www.linguee.',
                                                                           'yelp.com',
                                                                           'www.tripadvisor',
                                                                           'soundcloud.com',
                                                                           'www.gettyimages.',
                                                                           'groupdating.club',
                                                                           'www.ancestry.com',
                                                                           'https://translate.google.com',
                                                                           'www.ziprecruiter.com',
                                                                           '200.88.114.33',
                                                                           'merriam-webster.com',
                                                                           'spotify.com',
                                                                           'prezi.com',
                                                                           'classroom.google.com',
                                                                           'www.espn.com',
                                                                           'www.geeksforgeeks.org',
                                                                           'www.quora.com',
                                                                           'support.google.com',
                                                                           'www.airbnb.',
                                                                           'www.expedia.',
                                                                           'www.tutorialspoint.com',
                                                                           'moovitapp.com',
                                                                           'mapquest.com',
                                                                           'www.opentable.com',
                                                                           'outlook.live.com',
                                                                           'www.carinsuranceguidebook.',
                                                                           '419scam.org',
                                                                           'www.abercrombie.',
                                                                           'www.helpwanted.',
                                                                           'pornhub',
                                                                           'xnxx',
                                                                           'playboy',
                                                                           'xvideos.com',
                                                                           'torrent',
                                                                           'porno',
                                                                           'play.google.com',
                                                                           'films',
                                                                           'movies',
                                                                           'boob',
                                                                           'xporn',
                                                                           'dirtyporn',
                                                                           '\\.tk',
                                                                           'imgur.com',
                                                                           'www.waitrose.com',
                                                                           'twitch.tv',
                                                                           'celllookups.com',
                                                                           'www.researchgate.net',
                                                                           'www.mlb.com',
                                                                           'rstudio.com',
                                                                           'tumblr.com',
                                                                           '\\.gz',
                                                                           'https://scholar.google.com/citations?',
                                                                           'www.dreamville.com/',
                                                                           'www.learn-c.org',
                                                                           'www.kaggle.com',
                                                                           'www.cprogramming.com',
                                                                           'www.jcrew.com',
                                                                           'r-project.org',
                                                                           'www.apartments.com',
                                                                           'www.imdb.com',
                                                                           'science.sciencemag.org/content',
                                                                           'krecs.com',
                                                                           'https://qz.com/1302211/haitch-or-aitch-english-speakers-cant-agree-on-how-to-say-h/',
                                                                           'http://dev.stein.cl/sli/apertura/FormDapi.aspx?User=CTAMAYO&IdEjec=CTS',
                                                                           'www.shutterstock.com',
                                                                           'https://books.google.com',
                                                                           'quizlet.com',
                                                                           'gsuite.google.com',
                                                                           'www.vocabulary.com',
                                                                           'https://sites.google.com/site/hj7cbm27/ConsumerElectronics/etraders',
                                                                           '\\.xls',
                                                                           '\\.xlsx',
                                                                           '\\.pdf',
                                                                           '\\.doc',
                                                                           '\\.docx',
                                                                           '\\.jpg',
                                                                           '\\.ppsx',
                                                                           '\\.jpeg',
                                                                           '\\.mp4',
                                                                           '\\.mp3',
                                                                           'ftp://'],
                                         'websites': ['bloomberg.com/profile/company',
                                                      'reuters.com/companies/',
                                                      'emis.com/php/company-profile']},
                              {'language': ['en'], 'date_range': None}
                              ),
                             ('entity', {'nm_root': 'root/path',
                                         'service': 'googlenews',
                                         'or_combine_kw': True,
                                         'or_combine_websites': True,
                                         'proxy_account': 'account_name',
                                         'refresh_period': {'days': 0, 'months': 6, 'years': 0},
                                         'keywords': {'en': ['money laundering',
                                                             'ponzi scheme',
                                                             'smuggling',
                                                             'tax evasion',
                                                             'terrorism',
                                                             'trafficking',
                                                             'bribery',
                                                             'convicted',
                                                             'corruption',
                                                             'embezzlement',
                                                             'narcotic',
                                                             'arrested',
                                                             'fraud',
                                                             'indicted',
                                                             'indictment',
                                                             'jailed',
                                                             'lawsuit'],
                                                      'es': ['terrorismo',
                                                             'blanqueo de dinero',
                                                             'lavado de dinero',
                                                             'crimen financiero',
                                                             'delito financiero',
                                                             'narcotráfico',
                                                             'corrupción',
                                                             'comercio con personas',
                                                             'esquema ponzi',
                                                             'evasión fiscal',
                                                             'fraude',
                                                             'malversación',
                                                             'desfalco',
                                                             'soborno',
                                                             'terrorista',
                                                             'contrabando',
                                                             'acusado',
                                                             'acusada',
                                                             'condenado',
                                                             'condenada',
                                                             'detenido',
                                                             'detenida',
                                                             'encarcelado',
                                                             'encarcelada',
                                                             'indiciado',
                                                             'indiciada',
                                                             'demanda judicial']},
                                         'keywords_excluded': {'en': [], 'es': []},
                                         'url_filter_exclusion_patterns': ['facebook.com',
                                                                           'linkedin.com',
                                                                           'twitter.com',
                                                                           'instagram.com',
                                                                           'www.glassdoor.',
                                                                           'www.indeed.',
                                                                           'www.britannica.com',
                                                                           'myspace',
                                                                           'youtube.com',
                                                                           'wikipedia',
                                                                           'pinterest',
                                                                           'reddit',
                                                                           'amazon.com',
                                                                           'alibaba.com',
                                                                           'github.com',
                                                                           'dictionary.',
                                                                           'wiktionary.org',
                                                                           'www.linguee.',
                                                                           'yelp.com',
                                                                           'www.tripadvisor',
                                                                           'soundcloud.com',
                                                                           'www.gettyimages.',
                                                                           'groupdating.club',
                                                                           'www.ancestry.com',
                                                                           'https://translate.google.com',
                                                                           'www.ziprecruiter.com',
                                                                           '200.88.114.33',
                                                                           'merriam-webster.com',
                                                                           'spotify.com',
                                                                           'prezi.com',
                                                                           'classroom.google.com',
                                                                           'www.espn.com',
                                                                           'www.geeksforgeeks.org',
                                                                           'www.quora.com',
                                                                           'support.google.com',
                                                                           'www.airbnb.',
                                                                           'www.expedia.',
                                                                           'www.tutorialspoint.com',
                                                                           'moovitapp.com',
                                                                           'mapquest.com',
                                                                           'www.opentable.com',
                                                                           'outlook.live.com',
                                                                           'www.carinsuranceguidebook.',
                                                                           '419scam.org',
                                                                           'www.abercrombie.',
                                                                           'www.helpwanted.',
                                                                           'pornhub',
                                                                           'xnxx',
                                                                           'playboy',
                                                                           'xvideos.com',
                                                                           'torrent',
                                                                           'porno',
                                                                           'play.google.com',
                                                                           'films',
                                                                           'movies',
                                                                           'boob',
                                                                           'xporn',
                                                                           'dirtyporn',
                                                                           '\\.tk',
                                                                           'imgur.com',
                                                                           'www.waitrose.com',
                                                                           'twitch.tv',
                                                                           'celllookups.com',
                                                                           'www.researchgate.net',
                                                                           'www.mlb.com',
                                                                           'rstudio.com',
                                                                           'tumblr.com',
                                                                           '\\.gz',
                                                                           'https://scholar.google.com/citations?',
                                                                           'www.dreamville.com/',
                                                                           'www.learn-c.org',
                                                                           'www.kaggle.com',
                                                                           'www.cprogramming.com',
                                                                           'www.jcrew.com',
                                                                           'r-project.org',
                                                                           'www.apartments.com',
                                                                           'www.imdb.com',
                                                                           'science.sciencemag.org/content',
                                                                           'krecs.com',
                                                                           'https://qz.com/1302211/haitch-or-aitch-english-speakers-cant-agree-on-how-to-say-h/',
                                                                           'http://dev.stein.cl/sli/apertura/FormDapi.aspx?User=CTAMAYO&IdEjec=CTS',
                                                                           'www.shutterstock.com',
                                                                           'https://books.google.com',
                                                                           'quizlet.com',
                                                                           'gsuite.google.com',
                                                                           'www.vocabulary.com',
                                                                           'https://sites.google.com/site/hj7cbm27/ConsumerElectronics/etraders',
                                                                           '\\.xls',
                                                                           '\\.xlsx',
                                                                           '\\.pdf',
                                                                           '\\.doc',
                                                                           '\\.docx',
                                                                           '\\.jpg',
                                                                           '\\.ppsx',
                                                                           '\\.jpeg',
                                                                           '\\.mp4',
                                                                           '\\.mp3',
                                                                           'ftp://'],
                                         'websites': []},
                              {'language': ['en'], 'date_range': None}
                              ),
                         ])
def test_assign_query_gen_inputs(searchservice, entity, business_configuration, client_search_configs):
    """
    note that the client config for language is en, while the business config can have multiple languages for the
    keywords. In test__query_gen, the queries should only have the client config language
    """
    query_params = searchservice._assign_query_gen_inputs(entity, business_configuration, client_search_configs)
    assert query_params == {'entity': [entity],
                            'keywords': business_configuration['keywords'],
                            'language': client_search_configs['language'],
                            'websites': business_configuration['websites'],
                            'or_combine_kw': business_configuration['or_combine_kw'],
                            'or_combine_websites': business_configuration['or_combine_websites'],
                            'keywords_excluded': business_configuration['keywords_excluded'],
                            'date_range': client_search_configs['date_range']}
    print(business_configuration)
    print(query_params)


@pytest.mark.parametrize('query_params, business_configuration, query_output', [(
        {'entity': ['entity'],
         'keywords': {'en': ['', 'company profile']},
         'language': ['en'],
         'websites': ['bloomberg.com/profile/company',
                      'reuters.com/companies/',
                      'emis.com/php/company-profile'],
         'or_combine_kw': False,
         'or_combine_websites': False,
         'keywords_excluded': {'en': []},
         'date_range': None
         },
        {'lob_root': 'root/path',
         'service': 'google',
         'or_combine_kw': False,
         'or_combine_websites': False,
         'proxy_account': 'account_name',
         'refresh_period': {'days': 0, 'months': 6, 'years': 0},
         'keywords': {'en': ['', 'company profile']},
         'keywords_excluded': {'en': []},
         'url_filter_exclusion_patterns': ['facebook.com',
                                           'linkedin.com',
                                           'twitter.com',
                                           'instagram.com',
                                           'www.glassdoor.',
                                           'www.indeed.',
                                           'www.britannica.com',
                                           'myspace',
                                           'youtube.com',
                                           'wikipedia',
                                           'pinterest',
                                           'reddit',
                                           'amazon.com',
                                           'alibaba.com',
                                           'github.com',
                                           'dictionary.',
                                           'wiktionary.org',
                                           'www.linguee.',
                                           'yelp.com',
                                           'www.tripadvisor',
                                           'soundcloud.com',
                                           'www.gettyimages.',
                                           'groupdating.club',
                                           'www.ancestry.com',
                                           'https://translate.google.com',
                                           'www.ziprecruiter.com',
                                           '200.88.114.33',
                                           'merriam-webster.com',
                                           'spotify.com',
                                           'prezi.com',
                                           'classroom.google.com',
                                           'www.espn.com',
                                           'www.geeksforgeeks.org',
                                           'www.quora.com',
                                           'support.google.com',
                                           'www.airbnb.',
                                           'www.expedia.',
                                           'www.tutorialspoint.com',
                                           'moovitapp.com',
                                           'mapquest.com',
                                           'www.opentable.com',
                                           'outlook.live.com',
                                           'www.carinsuranceguidebook.',
                                           '419scam.org',
                                           'www.abercrombie.',
                                           'www.helpwanted.',
                                           'pornhub',
                                           'xnxx',
                                           'playboy',
                                           'xvideos.com',
                                           'torrent',
                                           'porno',
                                           'play.google.com',
                                           'films',
                                           'movies',
                                           'boob',
                                           'xporn',
                                           'dirtyporn',
                                           '\\.tk',
                                           'imgur.com',
                                           'www.waitrose.com',
                                           'twitch.tv',
                                           'celllookups.com',
                                           'www.researchgate.net',
                                           'www.mlb.com',
                                           'rstudio.com',
                                           'tumblr.com',
                                           '\\.gz',
                                           'https://scholar.google.com/citations?',
                                           'www.dreamville.com/',
                                           'www.learn-c.org',
                                           'www.kaggle.com',
                                           'www.cprogramming.com',
                                           'www.jcrew.com',
                                           'r-project.org',
                                           'www.apartments.com',
                                           'www.imdb.com',
                                           'science.sciencemag.org/content',
                                           'krecs.com',
                                           'https://qz.com/1302211/haitch-or-aitch-english-speakers-cant-agree-on-how-to-say-h/',
                                           'http://dev.stein.cl/sli/apertura/FormDapi.aspx?User=CTAMAYO&IdEjec=CTS',
                                           'www.shutterstock.com',
                                           'https://books.google.com',
                                           'quizlet.com',
                                           'gsuite.google.com',
                                           'www.vocabulary.com',
                                           'https://sites.google.com/site/hj7cbm27/ConsumerElectronics/etraders',
                                           '\\.xls',
                                           '\\.xlsx',
                                           '\\.pdf',
                                           '\\.doc',
                                           '\\.docx',
                                           '\\.jpg',
                                           '\\.ppsx',
                                           '\\.jpeg',
                                           '\\.mp4',
                                           '\\.mp3',
                                           'ftp://'],
         'websites': ['bloomberg.com/profile/company',
                      'reuters.com/companies/',
                      'emis.com/php/company-profile']
         },
        [
            {'entity': 'entity',
             'url': 'https://www.google.com/search?safe=strict&q=%22entity%22+%22%22+site%3Abloomberg.com/profile'
                    '/company',
             'cache_url': '', 'retries': 0, 'response_encoding': None, 'language': 'en',
             'proxy_account': 'account_name'},
            {'entity': 'entity',
             'url': 'https://www.google.com/search?safe=strict&q=%22entity%22+%22%22+site%3Areuters.com/companies/',
             'cache_url': '', 'retries': 0, 'response_encoding': None, 'language': 'en',
             'proxy_account': 'account_name'},
            {'entity': 'entity',
             'url': 'https://www.google.com/search?safe=strict&q=%22entity%22+%22%22+site%3Aemis.com/php/company-profile',
             'cache_url': '', 'retries': 0, 'response_encoding': None, 'language': 'en',
             'proxy_account': 'account_name'},
        ])])
def test__query_gen(searchservice, query_params, business_configuration, query_output):
    queries = []
    for i in searchservice._query_gen(business_configuration, **query_params):
        queries.append(i)
    if not query_params['or_combine_kw']:
        for query, query_out in zip(queries, query_output):
            for key in query.keys():
                assert key in query_out
                assert query[key] == query_out[key]


# if searchservice.service == 'google' and 'www.google.com' in \
#         searchservice.search_service_option[searchservice.language[0]]['start_url']:
#     assert [{'entity': 'JOHN DOE',
#              'url': 'https://www.google.com/search?safe=strict&q=%22JOHN+DOE%22+AND+%28%22arrested%22+OR+'
#                     '%22money+laundering%22%29+',
#              'cache_url': '',
#              'response_encoding': None,
#              'language': 'en',
#              'retries': 0},
#             {'entity': 'JANE DOE',
#              'url': 'https://www.google.com/search?safe=strict&q=%22JANE+DOE%22+AND+%28%22arrested%22+OR+'
#                     '%22money+laundering%22%29+',
#              'cache_url': '',
#              'response_encoding': None,
#              'language': 'en',
#              'retries': 0}
#             ] == [i for i in searchservice._query_gen()]
# else:
#     assert [
#                {'entity': 'JOHN DOE',
#                 'url': 'https://news.google.com/search?q=%22JOHN+DOE%22+%22arrested%22+site%3Aexample.com+%20-excluded'
#                        '&hl=es-419&gl=US&ceid=US:es-419+',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JOHN DOE',
#                 'url': 'https://news.google.com/search?q=%22JOHN+DOE%22+%22arrested%22++%20-excluded&hl=es-419'
#                        '&gl=US&ceid=US:es-419',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JOHN DOE',
#                 'url': 'https://news.google.com/search?q=%22JOHN+DOE%22+%22money+laundering%22+site%3Aexample.com'
#                        '%20-excluded&hl=es-419&gl=US&ceid=US:es-419+',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JOHN DOE',
#                 'url': 'https://news.google.com/search?q=%22JOHN+DOE%22+%22money+laundering%22+%20-excluded'
#                        '&hl=es-419&gl=US&ceid=US:es-419',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JANE DOE',
#                 'url': 'https://news.google.com/search?q=%22JANE+DOE%22+%22arrested%22+site%3Aexample.com+%20-excluded'
#                        '&hl=es-419&gl=US&ceid=US:es-419+',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JANE DOE',
#                 'url': 'https://news.google.com/search?q=%22JANE+DOE%22+%22arrested%22++%20-excluded&hl=es-419&gl=US'
#                        '&ceid=US:es-419',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JANE DOE',
#                 'url': 'https://news.google.com/search?q=%22JANE+DOE%22+%22money+laundering%22+site%3Aexample.com'
#                        '%20-excluded&hl=es-419&gl=US&ceid=US:es-419+',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0},
#                {'entity': 'JANE DOE',
#                 'url': 'https://news.google.com/search?q=%22JANE+DOE%22+%22money+laundering%22+%20-excluded'
#                        '&hl=es-419&gl=US&ceid=US:es-419',
#                 'cache_url': '',
#                 'response_encoding': None,
#                 'language': 'es',
#                 'retries': 0}
#            ] == [i for i in searchservice._query_gen()]


@pytest.mark.parametrize('words, space', [(None, ' '), ('', ' '), ('hello', ' '), ('hello world', ' ')])
def test__encode_make_phrase(searchservice, words, space):
    if not words:
        assert not searchservice._encode_make_phrase(words, space)
    else:
        assert '%22{0}%22{1}'.format(words.replace(' ', '+').replace('&', '%26'), space) == \
               searchservice._encode_make_phrase(words, space)


@pytest.mark.parametrize('websites, or_combine_websites',
                         [(["bloomberg.com/profile/company",
                            "reuters.com/companies/",
                            "emis.com/php/company-profile"
                            ], False),
                          (["bloomberg.com/profile/company",
                            "reuters.com/companies/",
                            "emis.com/php/company-profile"
                            ], True),
                          ([], False),
                          ])
def test__encode_site_search(searchservice, websites, or_combine_websites):
    if not websites:
        assert next(searchservice._encode_site_search(websites, or_combine_websites)) == ''
    elif not or_combine_websites:
        assert [i for i in searchservice._encode_site_search(websites, or_combine_websites)] == [
            f"site%3A{site}" if site else '' for site in
            websites]
    elif websites and or_combine_websites:
        assert next(searchservice._encode_site_search(websites, or_combine_websites)) == \
               'site' + '%3A' + '%20OR%20site%3A'.join(map(str, websites))


@pytest.mark.parametrize('keywords_excluded', [[], ['a', 'b', 'c']])
def test__encode_keywords_excluded(searchservice, keywords_excluded):
    if not keywords_excluded:
        assert searchservice._encode_keywords_excluded(keywords_excluded) == ''
    else:
        assert searchservice._encode_keywords_excluded(keywords_excluded) == ''.join(
            '%20-' + i for i in keywords_excluded)


@pytest.mark.parametrize('date_range', ['', None, 'anytime', 'a', 'hour', 'h', 'day', 'd', 'week', 'w', 'month',
                                        'm', 'year', 'y', '01/01/2020,02/03/2020', '02/03/2020-01/01/2020',
                                        '02/03/2020 01/01/2020', 'exception'])
def test__encode_date_ranges(searchservice, date_range):
    # re-assign date range for each test
    date_ranges = [date_range] if not isinstance(date_range, list) else date_range
    pre_string = '&tbs=qdr%3A'

    # if not date_range:
    #     assert next(searchservice._encode_date_ranges(date_ranges)) == ''
    # else:
    for date_range in date_ranges:
        if (date_range is None) or (len(date_range) == 0):
            assert next(searchservice._encode_date_ranges(date_ranges)) == '' ''
        elif date_range in ['a', 'anytime']:
            assert next(searchservice._encode_date_ranges(date_range)) == '&tbas=0'
        elif date_range != 'exception' and date_range.isalpha():
            assert next(searchservice._encode_date_ranges(date_range)) == pre_string + date_range[0]
        elif not date_range.isalpha():
            if ',' in date_range:
                date1, date2 = date_range.split(',')
            elif ' ' in date_range:
                date1, date2 = date_range.split(' ')
            else:
                date1, date2 = date_range.split('-')
            date1_check = datetime.strptime(date1, '%m/%d/%Y')
            date2_check = datetime.strptime(date2, '%m/%d/%Y')
            if date2_check < date1_check:
                date1, date2 = date2, date1
            date1.replace('/', '%2F')
            date2.replace('/', '%2F')
            assert next(searchservice._encode_date_ranges(
                [date_range])) == '&tbs=cdr%3A1%2Ccd_min%3A' + date1 + '%2Ccd_max%3A' + date2
        elif date_range == 'exception':
            # with pytest.raises(ValueError) as exc:
            assert next(searchservice._encode_date_ranges([date_range])) == ''


@pytest.mark.parametrize('keywords, degree', [(['a', 'b', 'c', 'd'], 1), (['a', 'b', 'c', 'd'], 2), ([], 0)])
def test__encode_keyword_combos(searchservice, keywords, degree):
    if keywords and degree == 1:
        assert [i for i in searchservice._encode_keyword_combos(keywords, degree)] == [("%22a%22", 'a'),
                                                                                       ("%22b%22", 'b'),
                                                                                       ("%22c%22", 'c'),
                                                                                       ("%22d%22", 'd'),
                                                                                       ]
    elif keywords and degree == 2:
        assert [i for i in searchservice._encode_keyword_combos(keywords, degree)] == [("%22a%22%20%22b%22", 'a b'),
                                                                                       ("%22a%22%20%22c%22", 'a c'),
                                                                                       ("%22a%22%20%22d%22", 'a d'),
                                                                                       ("%22b%22%20%22c%22", 'b c'),
                                                                                       ("%22b%22%20%22d%22", 'b d'),
                                                                                       ("%22c%22%20%22d%22", 'c d')]
    else:
        assert next(searchservice._encode_keyword_combos(keywords, degree)) == ('%20', '%20')


def test__type_checking():
    # assert False
    pass
