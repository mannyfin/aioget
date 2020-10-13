from datetime import datetime
# import logging
from bs4 import BeautifulSoup
import json
from tldextract import tldextract
from deprecated.sphinx import deprecated

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger
from core.utils import pop_arb_field_if_exists, set_arb

basiclogger = logger.rabbit_logger(__name__)


# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# handler = logging.StreamHandler(sys.stdout)
# formatter = logging.Formatter('%(asctime)s %(levelname)-6s [%(filename)-s: %(lineno)d] %(message)s',
#                               datefmt='%Y-%m-%d %H:%M')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# todo cleanup


def parse(**kwargs) -> dict:
    """
     .. todo:: cleanup and get a better test url... can make this faster too.

    Args:
        **kwargs:

    Returns:

    """
    error_str = ''
    language = kwargs['language']
    entity = kwargs['entity']
    search_url = kwargs['url']
    cache_url = kwargs['cache_url']  # should be an empty string
    response = kwargs['response']  # should be a string or None
    arb, kwargs = pop_arb_field_if_exists(kwargs)

    # entity, _ = args
    # if isinstance(entity, str):
    #     entity = [entity]
    todaysdate = datetime.today().date().isoformat()
    urls = []
    cache_urls = []
    try:
        if not response:
            # print('None', {'parsed_output': [entity] + [todaysdate, language, ';'.join(urls), ';'.join(cache_urls),
            #                                             search_url],
            #                'error': f'EMPTY_RESPONSE|{search_url}'})
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

        # logger.debug(response.url)
        soup = BeautifulSoup(response, 'lxml')
        articles = soup.find_all('article')

        if not articles:
            # return {'parsed_output': [entity] + [todaysdate, language, ';'.join(urls), ';'.join(cache_urls), search_url],
            #         'error': error_str}
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

    except Exception as exc:
        basiclogger.error(exc.__repr__())
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

    # find all script tags
    scripts = soup.find_all('script')
    idx = 0
    # find the script tag where the article is located. It is not always the same element.
    for article in articles:
        href_article = article.a['href']
        for idx, script in enumerate(scripts):
            if href_article.split('/')[-1].split('?')[0] in f"{script}":
                # print('script', idx)
                break
        script_idx = idx

        # convert script tag to string and break on double brackets
        sbrack = f"{scripts[script_idx]}".split('[[')
        # split by commas for each bracketed element, and then search the href to find the right elements
        scom = [i.split(',') for i in sbrack]
        indices = []
        for idx, s in enumerate(scom):
            for j in s:
                if href_article.split('/')[-1].split('?')[0] in j:
                    # print('find', idx)
                    indices.append(idx)
                    # break
        # for each list of elements found above, now check that it's a url and non-google domain. If so, then append
        for index in indices:
            keep_iterating = True
            for element in scom[index]:
                if '"http' in element and tldextract.extract(element.replace('"', '')).domain != 'google':
                    # print('http', element)
                    urls.append(element.replace('"', ''))
                    cache_urls.append('')
                    keep_iterating = False
                    break
            if not keep_iterating:
                break

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
