from datetime import datetime
from bs4 import BeautifulSoup
# import logging
from lxml import html as lhtml

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger
from core.utils import pop_arb_field_if_exists, set_arb

basiclogger = logger.rabbit_logger(__name__)


def parse(*args, **kwargs) -> dict:  # self, response, args):
    """
    If search results exist, it will parse each result into a dictionary of {key: [list of results]} where each key
    is a query

    If search results do not exist (i.e. if Google returns something such as: "Your search ... - did not match any
    documents" then the response.xpath returns an empty list.

    # Depending on whether the search is conducted locally or over proxy, the Google search result webpage
    # is slightly different

    # this xpath works locally
    search_results = response.xpath('//div["main"]//div[div[a[starts-with(@href, "/url?q") and
    not('contains(@href, "accounts.google.com"))]]]').getall()

    # this xpath works on crawlera
    search_results = response.xpath('//div[@class="r"]/parent:: backslashSTAR_SYMBOL').getall()

    .. todo:: cleanup

    Args:
        *args:
        **kwargs:

    Returns:
        dict: string output, error

    """
    error_str = ''
    language = kwargs['language']
    entity = kwargs['entity']
    search_url = kwargs['url']
    cache_url = kwargs['cache_url']  # should be an empty string
    html = kwargs['response']  # should be a string or None

    arb, kwargs = pop_arb_field_if_exists(kwargs)
    todaysdate = datetime.today().date().isoformat()

    urls = []
    cache_urls = []
    if not html:
        # return {'parsed_output': entity + [todaysdate, language, ';'.join(urls), ';'.join(cache_urls), search_url],
        #         'error': f'EMPTY_RESPONSE|{search_url}'}
        outmsg = {'entity': entity,
                  'date': todaysdate,
                  'language': language,
                  'urls': urls,
                  'cache_urls': cache_urls,
                  'search_url': search_url,
                  'error': 'EMPTY_RESPONSE',
                  'client': kwargs['client'],
                  'business_function': kwargs['business_function']
                  }
        outmsg = set_arb(outmsg, arb)
        return outmsg

    try:

        soup = BeautifulSoup(html, 'lxml')

        check1 = 'did not match any documents' in soup.find('div', {'id': 'topstuff'})
        if hasattr(check1, 'text'):
            check1 = check1.text
        check2 = 'No results found' in soup.find('div', {'id': 'topstuff'}).text
        if hasattr(check2, 'text'):
            check2 = check2.text

        if check1 or check2:
            basiclogger.info(f'No results found: {search_url}')

        else:
            tree = lhtml.fromstring(html)
            # todo this will get some extra links...may be useful in the future
            # search_results = tree.xpath('//div[@class="r"]/parent::*//@href')

            # search_results = tree.xpath('//div[@class="r"]/*//@href')

            # cashit = False
            # for idx, element in enumerate(search_results):
            #     if not idx:
            #         urls.append(element.replace('/search?safe=strict&q=related:', ''))
            #     elif element == '#':  # cash in on some pounds if your british
            #         cashit = True
            #     elif cashit:
            #         cache_urls.append(element.replace('/search?safe=strict&q=related:', ''))
            #         cashit = False
            #     elif len(urls) == len(cache_urls):
            #         urls.append(element.replace('/search?safe=strict&q=related:', ''))
            #     elif len(urls) == 1 + len(cache_urls):
            #         urls.append(element.replace('/search?safe=strict&q=related:', ''))
            #         cache_urls.append('')
            search_results = tree.xpath('//div[@id="search"]/*//@href')

            # cashit = False
            for idx, element in enumerate(search_results):
                elrepl = element.replace('/search?safe=strict&q=related:', '')
                if 'http' not in elrepl[:4]:
                    continue
                if not idx:
                    urls.append(elrepl)
                elif element == '#':  # cash in on some pounds if your british
                    # cashit = True
                    continue
                elif 'webcache.googleusercontent' in element:
                    cache_urls.append(elrepl)
                    # cashit = False
                elif len(urls) == len(cache_urls):
                    urls.append(elrepl)
                elif len(urls) == 1 + len(cache_urls):
                    urls.append(elrepl)
                    cache_urls.append('')

    except Exception as exc:
        # default case is to add {key:[]}
        # print('\n\n\n\nNew edge case found: ', str(entity), response.url, '\n\n\n\n')
        basiclogger.error(f'\n\n\n\nNew edge case found: {entity}|{search_url}\n\n\n\n')
        error_str = f'PARSER_EDGE_CASE|{search_url}'
        pass

    # output = '|'.join(entity + [todaysdate, self.language, ';'.join(urls), ';'.join(cache_urls)])
    # 'parsed_output': [entity] + [todaysdate, language, ';'.join(urls), ';'.join(cache_urls), search_url],
    outmsg = {'entity': entity,
              'date': todaysdate,
              'language': language,
              'urls': urls,
              'cache_urls': cache_urls,
              'search_url': search_url,
              'error': error_str,
              'client': kwargs['client'],
              'business_function': kwargs['business_function']
              }

    outmsg = set_arb(outmsg, arb)
    return outmsg
