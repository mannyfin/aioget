import asyncio
from datetime import datetime
from itertools import combinations
import json
import glob
import os
import time
from typing import Optional, Tuple
import re
import sys

from aiohttp.client import ClientSession, TCPConnector
import redis

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from configs.base.consts import CONFIG_DIR, ASYNC_SLEEP
from core import logger
from core import async_queue, filtration, async_write
from core.async_requests import AsyncHttpRequests
from core.utils import load_config, parse_consumer, make_config, pop_arb_field_if_exists, set_arb
from parser_scripts import google, googlenews


from sys import platform
if platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


basiclogger = logger.rabbit_logger(__name__)


# todo or_combine_sites param -> lob searches -> measure perf impact

class SearchService(object):
    """
    The Search Service is a generic class that is used by any process in order to accept search inputs (e.g. search
    terms, keywords, sites, etc.), perform searches, and pass the results to another service. The Search Service
    implements a search query generator + async http requests + webpage Data Parser (google or googlenews) + async
    write to write outputs to a file.
    """
    SEARCH_SERVICE_CONFIG_PATH = os.path.normpath(os.path.join(CONFIG_DIR, 'service', 'search.json'))  # Proxy info, search sites, etc.
    BUSINESS_CONFIGS_DIR = os.path.normpath(os.path.join(CONFIG_DIR, 'business_drivers', 'search'))  # NegMedia/SJA/LOB/etc
    CLIENT_CONFIGS_DIR = os.path.normpath(os.path.join(CONFIG_DIR, 'client'))

    BUSINESS_CONFIGS_PATHS = glob.glob(os.path.join(BUSINESS_CONFIGS_DIR, '*.json'))
    CLIENT_CONFIGS_PATHS = glob.glob(os.path.join(CLIENT_CONFIGS_DIR, '*', '*.json'))

    def __init__(self, input_queue: asyncio.Queue, publish_queue: asyncio.Queue):
        """

        Args:
            input_queue:
            publish_queue:
        """
        self.service_configs = load_config(self.SEARCH_SERVICE_CONFIG_PATH)
        self.business_configs = make_config(self.BUSINESS_CONFIGS_PATHS)
        self.client_configs = make_config(self.CLIENT_CONFIGS_PATHS)
        # todo pass in only the required params
        self.async_http_requests = AsyncHttpRequests(**self.service_configs)
        self.input_queue = input_queue
        self.publish_queue = publish_queue
        self.config_refresh = time.time()

        ##################3
        # self.service_configs['redis_db_params']['host'] = 'localhost'

        self.search_history = redis.Redis(**self.service_configs['redis_db_params'])

    def start(self):
        """
        Starts the Search Service by creating a worker daemons for each number of TCP connections for the desired
        concurrency. After a worker completes a url request, it sends the response to a webpage parser, which extracts
        the urls. Finally, the extracted urls are individually placed on messages for another service.

        Issues are saved in an audit file for review

        Returns:
            workers, queues, session
        """
        # use an intermediate queue here to limit number of messages waiting in the service.
        query_queue = async_queue.get_queue(maxsize=200)
        parse_queue = async_queue.get_queue()
        write_queue = async_queue.get_queue()

        # async with ClientSession(connector=TCPConnector(limit=self.async_http_requests.connections, ssl=False)) as \
        #         session:
        session = ClientSession(connector=TCPConnector(limit=self.async_http_requests.connections, ssl=False))
        workers = []
        for _ in range(self.async_http_requests.connections):
            task = asyncio.create_task(self.put_onto_query_queue(query_queue)
                                       )
            workers.append(task)
            task = asyncio.create_task(async_queue.worker(query_queue, parse_queue,
                                                          self.async_http_requests.handle_requests,
                                                          session=session,
                                                          )
                                       )
            workers.append(task)
        task = asyncio.create_task(parse_consumer(next_queue=parse_queue, write_queue=write_queue,
                                                  ))
        workers.append(task)

        task = asyncio.create_task(
            self.write_consumer(audit_path='audit.txt', write_queue=write_queue, publish_queue=self.publish_queue)
            )
        workers.append(task)

        queues = [self.input_queue, self.publish_queue, query_queue, parse_queue, write_queue]
        return workers, queues, session

    async def put_onto_query_queue(self, query_queue: asyncio.Queue):
        """
        Takes a message off of the input queue. Extracts the query and the service/business/client configuration and
        places it on the query queue

        Args:
            query_queue:

        Returns:

        """
        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            while self.input_queue.qsize():
                try:
                    if query_queue.full():
                        await asyncio.sleep(ASYNC_SLEEP)
                        continue
                    # if self.input_queue.qsize():
                    message: dict = await self.input_queue.get()
                    if isinstance(message, bytes):
                        message = json.loads(message)
                    basiclogger.info(message)
                    entity, business_configuration, client_search_configs = self.make_configuration(message)
                    query_params = self._assign_query_gen_inputs(entity, business_configuration, client_search_configs)

                    arb_fields, message = pop_arb_field_if_exists(message)

                    parse = google.parse if 'google' == business_configuration['service'] else googlenews.parse
                    # construct query from message fields and configs
                    for query in self._query_gen(business_configuration, **query_params):
                        query['parse_func'] = parse
                        query['client'] = message['client']
                        query['business_function'] = message['business_function']

                        # add any arb fields.
                        query = set_arb(msg=query, arb=arb_fields)

                        if filtration.filter_entities_redis(entity, query['language'], message['business_function'],
                                                            self.business_configs['search'][message['business_function']]['refresh_period'],
                                                            self.search_history):
                            await query_queue.put(query)
                        else:
                            basiclogger.info(f"entity combo searched recently: {entity}|"
                                             f"{query['language']}|{message['business_function']}")
                except Exception as exc:
                    basiclogger.error(exc.__repr__())
                self.input_queue.task_done()

            await asyncio.sleep(ASYNC_SLEEP)

    async def write_consumer(self, audit_path: str,
                             write_queue: asyncio.Queue,
                             publish_queue: Optional[asyncio.Queue]):
        """
         used by the Search Service only right now.

        .. todo:: this could be refactored by async_queue.worker

        Args:
            audit_path: path to audit file
            publish_queue:
            write_queue: asyncio.Queue where each queue item is a list of asyncio.Futures for parsing the responses

        Returns:

        """

        while True:
            await asyncio.sleep(ASYNC_SLEEP)
            futures = []
            for ctr in range(write_queue.qsize()):
                futures.append(write_queue.get_nowait())
                write_queue.task_done()
            while futures:
                for _ in asyncio.as_completed(futures):
                    parsed_output = await _

                    # await async_write.write_data(output_path, f"{'|'.join(parsed_output['parsed_output'])}\n", 'a',
                    #                              encoding=None)

                    regexp_entity = re.sub('\W+', '', parsed_output['entity']).upper()

                    # popping any arb field so it doesn't get saved in the search history
                    arb_field, parsed_output = pop_arb_field_if_exists(parsed_output)

                    self.search_history.set(f"{regexp_entity}|{parsed_output['language']}|{parsed_output['business_function']}", json.dumps(parsed_output))

                    if publish_queue and parsed_output:
                        try:
                            # if no articles were found with the search, don't publish a message.
                            if 'urls' in parsed_output and 'cache_urls' in parsed_output:
                                for url, cache_url in zip(parsed_output['urls'], parsed_output['cache_urls']):
                                    # check if url or cache_url is garbage

                                    keep_url = filtration.filter_garbage_url_search_result(url,
                                                                                           self.business_configs['search'][
                                                                                               parsed_output[
                                                                                                   'business_function']][
                                                                                               'url_filter_exclusion_patterns'])
                                    keep_cache_url = True  # default if no cache_url present
                                    if cache_url:
                                        keep_cache_url = filtration.filter_garbage_url_search_result(
                                            cache_url, self.business_configs['search'][parsed_output['business_function']]['url_filter_exclusion_patterns']
                                        )

                                    if keep_url and keep_cache_url:
                                        msg = {'url': url,
                                               'cache_url': cache_url,
                                               'client': parsed_output['client'],
                                               'business_function': parsed_output['business_function'],
                                               'date': parsed_output['date'],
                                               'language': parsed_output['language'],
                                               'entity': parsed_output['entity']
                                               }
                                        if arb_field:
                                            msg = set_arb(msg=msg, arb=arb_field)
                                        await publish_queue.put(msg)
                            else:
                                basiclogger.debug(f"No results found for: {parsed_output}")
                        except Exception as exc:
                            basiclogger.error(exc.__repr__())
                            basiclogger.info(f'error_parsed_output: {parsed_output}')

                    if 'error' in parsed_output and parsed_output['error']:
                        await async_write.write_data(audit_path, f"{parsed_output['error']}\n", 'a',
                                                     encoding=None)

                if futures:
                    futures = [i for i in futures if not i.done()]

    def _query_gen(self, business_configuration, **kwargs) -> dict:
        """
        Builds a query for Google search. Wraps the entity and the keyword in double quotes. Calls other helper
        functions for query creation.

        - Uses the language class attribute to incorporate language specific component to url.
        - The html encoded entities are created using the entities instance attribute called with
          the`_encode_make_phrase` method.
        - Combines all the keywords with quotes, spaces, and OR if applicable according to or_combine_kw  instance
          attribute and calling _encode_keyword_combos method
        - Creates `site:website` if websites provided as website
          instance attribute, and combines with OR if applicable and calling _encode_site_search method
        - Creates date to-from string if date range provided as the date_range instance attribute and calling
          ` _encode_date_ranges` method
        - Creates keywords_excluded string if they were provided in keywords_excluded
          instance attribute and calling _encode_keywords_excluded method.

        Args: entities (list): Entities list if user wanted to override self.entities

        Returns:
            Generator of dicts of (entity, query, cache_url, retries)

        Examples:

            Input:
                service = ‘google’
                entities = [“Joe Black”]
                keywords = {'es': [“crime”,”launder”]}
                or_combine_kw = True
                date_range=['w']
                keywords_exclusion = ['yahoo.com']
                websites = ['bloomberg.com']
                language = 'es'

            Output:

                Resulting URL:
                https://www.google.com/search?safe=strict&q="Joe Black" AND ("crime" OR "launder") site:bloomberg.com
                -yahoo.com&hl=es-419&gl=US&ceid=US:es-419&tbs=qdr:w

                Resulting URL (encoded):
                'https://www.google.com/search?safe=strict&q=%22Joe+Black%22+AND+%28%22crime%22+OR+%22launder%22%29+site
                %3Abloomberg.com%20-yahoo.com&hl=es-419&gl=US&ceid=US:es-419+&tbs=qdr%3Aw'
        """

        entities = kwargs['entity']
        # quote = '"'
        quote = '%22'
        # space = '%20'
        space = '+'

        # self.encoded_excluded_kw = self._encode_keywords_excluded()

        for language in kwargs['language']:
            start_url, host_lang = self._get_start_url_host_lang(language, business_configuration)
            encoded_excluded_kw = self._encode_keywords_excluded(kwargs['keywords_excluded'][language])
            if not kwargs['or_combine_kw']:
                for entity in entities:
                    for keyword in self._encode_keyword_combos(kwargs['keywords'][language]):
                        # todo could also replace US with MX, CL or other spanish speaking country.
                        #  Need to assess results though
                        for web in self._encode_site_search(kwargs['websites'], kwargs['or_combine_websites']):
                            for dates in self._encode_date_ranges([kwargs['date_range']]):
                                space2 = '' if not web and not dates else '+'
                                if len(keyword[1].split(' ')) == 1:
                                    # search for "ENTITY" keyword_one_word
                                    yield {'entity': entity,
                                           'url': f"{start_url}{self._encode_make_phrase(entity, space)}{quote}"
                                                  f"{keyword[1].replace(' ', '+')}{quote}{space}{web}{space}"
                                                  f"{encoded_excluded_kw}{host_lang}{space2}{dates}".strip('+'),
                                           'cache_url': '',
                                           'retries': 0,
                                           'response_encoding': None,
                                           'language': language,
                                           'proxy_account': business_configuration['proxy_account']
                                           }
                                else:
                                    # search for "ENTITY" "keyword with multiple words"
                                    yield {'entity': entity,
                                           'url': f"{start_url}{self._encode_make_phrase(entity, space)}"
                                                  f"{keyword[0].replace(' ', '+')}{space}{web}{encoded_excluded_kw}"
                                                  f"{host_lang}{space2}{dates}".strip('+'),
                                           'cache_url': '',
                                           'retries': 0,
                                           'response_encoding': None,
                                           'language': language,
                                           'proxy_account': business_configuration['proxy_account']
                                           }
            else:
                # TODO refactor this
                open_parens = '%28'
                close_parens = '%29'
                # for language in self.language:
                start_url, host_lang = self._get_start_url_host_lang(language, business_configuration)

                OR_keywords = '("' + '" OR "'.join(map(str, kwargs['keywords'][language])) + '")'
                # apply html encodings
                OR_keywords = OR_keywords.replace(' ', '+')\
                                         .replace('(', open_parens)\
                                         .replace(')', close_parens)\
                                         .replace('"', quote)

                # OR_keywords = OR_keywords.replace(' ', '+')
                # OR_keywords = OR_keywords.replace('(', open_parens)
                # OR_keywords = OR_keywords.replace(')', close_parens)
                # OR_keywords = OR_keywords.replace('"', quote)

                for entity in entities:
                    for web in self._encode_site_search(kwargs['websites'], kwargs['or_combine_websites']):
                        for dates in self._encode_date_ranges([kwargs['date_range']]):
                            space2 = '' if not web and not dates else '+'
                            yield {'entity': entity,
                                   'url': f"{start_url}{self._encode_make_phrase(entity, space)}AND{space}"
                                          f"{OR_keywords}{space}{web}{encoded_excluded_kw}{host_lang}{space2}"
                                          f"{dates}".strip('+'),
                                   'cache_url': '',
                                   'retries': 0,
                                   'response_encoding': None,
                                   'language': language,
                                   'proxy_account': business_configuration['proxy_account']
                                   }

    def update_configs(self):
        # todo this should be outside the class or in a base class
        # todo replace this with push notification
        now = time.time()
        # read in configs every hour
        if (now - self.config_refresh) / 3600 > 1:
            # Check if there are new configs
            # todo potential breakage if there are same outermost keys in the config files
            self.BUSINESS_CONFIGS_PATHS = glob.glob(os.path.join(self.BUSINESS_CONFIGS_DIR, '*.json'))
            self.CLIENT_CONFIGS_PATHS = glob.glob(os.path.join(self.CLIENT_CONFIGS_DIR, '*', '*.json'))

            self.service_configs = load_config(self.SEARCH_SERVICE_CONFIG_PATH)
            self.business_configs = make_config(self.BUSINESS_CONFIGS_PATHS)
            self.client_configs = make_config(self.CLIENT_CONFIGS_PATHS)

            self.async_http_requests = AsyncHttpRequests(**self.service_configs)

            self.config_refresh = time.time()
            basiclogger.info('search service configs updated')

    def check_configs(self, business_function, client):
        if business_function not in self.business_configs['search'] or \
                client not in self.client_configs[business_function]:
            self.update_configs()
            if business_function not in self.business_configs['search']:
                # todo for now default to negative media
                business_function = 'media'
            if client not in self.client_configs[business_function]:
                client = 'default'
        return business_function, client

    def make_configuration(self, message):
        """
        Extract configuration for a specific search

        Args:
            message (dict): JSON response message containing instructions on how to do a search
        Returns:

        """
        # todo this should be outside the class?
        entity = message['entity']
        client = message['client'] if 'client' in message else ''
        business_function = message['business_function']
        # check that client/business function exist in the configs. If not update. If still not, then provide a default
        business_function, client = self.check_configs(business_function, client)

        business_configuration = self.business_configs['search'][business_function]
        client_search_configs = self.client_configs[business_function][client]
        return entity, business_configuration, client_search_configs

    def _assign_query_gen_inputs(self, entity, business_configuration, client_search_configs):

        # entities: list = entities if entities else ['']  # _query_gen Need >=1 entity if looping over other params
        keywords: dict = client_search_configs['keywords'] if 'keywords' in client_search_configs else \
            business_configuration['keywords']

        language: list = client_search_configs['language'] if 'language' in client_search_configs else \
            list(keywords.keys())

        websites: list = client_search_configs['websites'] if 'websites' in client_search_configs else \
            business_configuration['websites']

        or_combine_websites: bool = client_search_configs['or_combine_websites'] if 'or_combine_websites' in client_search_configs else \
            business_configuration['or_combine_websites']

        or_combine_kw: bool = client_search_configs['or_combine_kw'] if 'or_combine_kw' in client_search_configs else \
            business_configuration['or_combine_kw']

        keywords_excluded: list = client_search_configs[
            'keywords_excluded'] if 'keywords_excluded' in client_search_configs else \
            business_configuration['keywords_excluded']

        # todo add date_range if passed as an arb message parameter
        date_range: list = client_search_configs['date_range'] if 'date_range' in client_search_configs else \
            business_configuration['date_range']
        query_params = {'entity': [entity],
                        'keywords': keywords,
                        'language': language,
                        'websites': websites,
                        'or_combine_kw': or_combine_kw,
                        'or_combine_websites': or_combine_websites,
                        'keywords_excluded': keywords_excluded,
                        'date_range': date_range}
        self._type_checking(**query_params)
        return query_params

    def _get_start_url_host_lang(self, language: str, business_configuration) -> Tuple[str, str]:
        """
        Read service configs to obtain the start_url and host_lang parameters

        Args:
            language (str): language for the search

        Returns:
            start_url (str): start_url for the TLD
            host_lang (str): language and geolocation-specific encoding applied to the url

        """
        options = self.service_configs['service_option'][business_configuration['service']][language]
        start_url = options['start_url']
        host_lang = options['host_lang']

        return start_url, host_lang

    @staticmethod
    def _encode_make_phrase(words: str, space: str):
        """
        Helper function. Makes a HTML encoded string using words and spaces using html encodings to replaces spaces and
        quotes with their % counterparts (ex. Space ('') = '+' and so on). Space variable can be anything to add
        after the double quotes following the word.

        Args:
            words (str): Word to make phrase with
            space (str): space

        Returns:
            empty string if word is None else word wrapped in quotes with space.
        """
        if not words:
            return ''
        else:
            return '%22{0}%22{1}'.format(words.replace(' ', '+').replace('&', '%26'), space)

    @staticmethod
    def _encode_site_search(websites: list, or_combine_websites: bool):
        """
        Adds site:http://www.website.com to Google search. If website == 'None', then default case is to NOT include
        site:example.com. This is useful if a search would like to search specific sites as well as not.

        Ex. `site:xyz.com` for one search and not including this string in another search.

        Returns:
            string  'site:website.com'  if websites else empty string

        """
        colon = '%3A'
        # default case, no websites
        if websites is None or len(websites) == 0:
            yield ''  # '%20'
        if not or_combine_websites:
            for website in websites:
                if website and not (website == 'None'):
                    yield 'site' + colon + website
                else:
                    yield ''  # '%20'
        else:
            if len(websites) == 1:
                yield 'site' + colon + websites[0]
            else:
                yield 'site' + colon + '%20OR%20site%3A'.join(map(str, websites))

    @staticmethod
    def _encode_keywords_excluded(keywords_excluded):
        """
        Generate string of filter keywords. This is to remove those keywords from search results.
        This is akin to typing: -excluded_kw1 -excluded_kw2 etc. In the search bar.

        Returns:
            string

        Examples:
            Input:
                keywords_excluded = ['a', 'b', 'c']

            Output:
                '%20-a%20-b%20-c'

        """
        # default case, no filter keywords
        if keywords_excluded is None or len(keywords_excluded) == 0:
            return ''  # '%20'

        if keywords_excluded is not None:
            return ''.join('%20-' + i for i in keywords_excluded)
        # and for any other weird reason
        # return ''  # '%20'

    @staticmethod
    def _encode_date_ranges(date_range: list):
        """
        Filter search results by date. Takes date_range list and parses the info inside and creates the string to be
        added to the query.

        Possible options for the element inside the date_range list are:
        
        - "anytime" or "a"
        - "hour" or "h"(past hour)
        - "day" or "d" (past day)
        - "week" or "w" (past week)
        - "month" or "m" (past month)
        - "year" or "y" (past year)
        - mm/dd/yyyy,mm/dd/yyyy (between two dates with earliest first)
            * The code handles the case where the two dates are out of order.
            * The delimeter between the two dates can be one of ‘,- ‘ (comma, hyphen or space)

        Returns:
            string with the HTML encoded date

        Examples:
            Input:
                date1, date2 are format mm/dd/yyyy,mm/dd/yyyy

            Output:
                '&tbs=cdr%3A1%2Ccd_min%3A' + date1 + '%2Ccd_max%3A' + date2
        """
        # if (date_range is None) or (len(date_range) == 0):
        #     yield ''  # '%20'
        # %3A is a colon :
        pre_string = '&tbs=qdr%3A'
        for date_entry in date_range:
            if (date_entry is None) or (not date_entry) or (isinstance(date_entry, list) and len(date_entry) == 0):
                yield ''
            elif date_entry == 'anytime' or date_entry == 'a':
                yield '&tbas=0'
            elif date_entry == 'hour' or date_entry == 'h':
                yield pre_string + 'h'
            elif date_entry == 'day' or date_entry == 'd':
                yield pre_string + 'd'
            elif date_entry == 'week' or date_entry == 'w':
                yield pre_string + 'w'
            elif date_entry == 'month' or date_entry == 'm':
                yield pre_string + 'm'
            elif date_entry == 'year' or date_entry == 'y':
                yield pre_string + 'y'
            else:
                try:
                    # if any, and find separator
                    if ',' in date_entry:
                        date1, date2 = date_entry.split(',')
                    elif ' ' in date_entry:
                        date1, date2 = date_entry.split(' ')
                    else:
                        date1, date2 = date_entry.split('-')
                    date1_check = datetime.strptime(date1, '%m/%d/%Y')
                    date2_check = datetime.strptime(date2, '%m/%d/%Y')
                    # check that dates are in order of min date , max date
                    if date2_check < date1_check:
                        date1, date2 = date2, date1
                    date1.replace('/', '%2F')
                    date2.replace('/', '%2F')
                    yield '&tbs=cdr%3A1%2Ccd_min%3A' + date1 + '%2Ccd_max%3A' + date2

                except Exception as exc:
                    basiclogger.info(exc)
                    # if all else fails, yield ''
                    yield ''  # '%20'

    @staticmethod
    def _encode_keyword_combos(keywords: list, degree: int = 1):
        """
        Generates tuples for combinations of keywords. See here for more information on how the degree works:
        https://en.wikipedia.org/wiki/Binomial_coefficient Most times we want to use degree=1. However, for research
        purposes we may want to test out different keyword combinations.

        Args:
            keywords (list): list of keywords. If provided from config file, provide self.keywords[language] to get
            the list
            degree (int): Degree of combinations (the k in n_choose_k from Probability & Statistics

        Returns:
            Generator tuples of form (comb(keywords,1), keyword)

        Examples:
            k = ['a', 'b', 'c', 'd']

            Input:
                combos(k,2)

            Output:
                ("a"%20"b", 'a b')
                ("a"%20"c", 'a c')
                ("a"%20"d", 'a d')
                ("b"%20"c", 'b c')
                ("b"%20"d", 'b d')
                ("c"%20"d", 'c d')
        """

        quote = '%22'
        if len(keywords) == 0:
            yield '%20', '%20'

        for x in list(combinations(keywords, degree)):
            if not x:
                # for empty string
                yield '%20', '%20'
            # yield ('"' + '"%20"'.join(x) + '"', ' '.join(x))
            yield quote + '%22%20%22'.join(x) + quote, ' '.join(x)

    @staticmethod
    def _type_checking(**kwargs):
        """
        Rudimentary type checking of input variables. This is run at the end of the __init__ instance of a class.

        Returns:
            None, if checked inputs pass given criteria
        """
        if (not isinstance(kwargs['entity'], list) or len(kwargs['entity']) == 0) and (
                not isinstance(kwargs['keywords'], dict)):
            raise ValueError('entities and keywords must both be lists with len >0')
        if not (isinstance(kwargs['keywords_excluded'], dict) or kwargs['keywords_excluded'] is None):
            raise TypeError('filter keywords must be of type == dict with the key a supported language string')
        if len(set(kwargs['keywords'])) < len(kwargs['keywords']):
            raise ValueError('Don\'t use duplicate keywords.')
        if kwargs['keywords_excluded'] is not None:
            for filtered in kwargs['keywords_excluded']:
                if len(filtered.replace(' ', '')) == 0:
                    raise ValueError('Don\'t use empty quotes or space in filter. '
                                     'Make sure there is no end line of file.')
