from bs4 import BeautifulSoup

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger
from core.utils import pop_arb_field_if_exists, set_arb

basiclogger = logger.rabbit_logger(__name__)


def parse(**kwargs) -> dict:
    """
    parse an open corporates webpage
    """
    parsed = {}
    try:
        url = kwargs['url']
        path = kwargs['encoded_url']
        arb, kwargs = pop_arb_field_if_exists(kwargs)

        with open(path, 'r') as f:
            resp = f.read()

        soup = BeautifulSoup(resp, 'lxml')
        # url = file_path.rsplit('/')[-1].split('.html')[0].replace('I', '/')
        # url = '/'.join([url.rsplit('/', 1)[0], url.rsplit('/', 1)[1].upper()])
        # rep = ''
        #     ent = soup.h1.text
        #     if soup.h1.a:
        #         rep = soup.h1.a.text
        #         ent = ent.replace(rep, '')
        #     entity = ent.strip()
        entity = [i for i in soup.h1][0].strip()

        table = soup.find_all('div', attrs={'id': 'attributes'})
        fields = [i.text.strip() for i in table[0].find_all('dt')]

        vals = [i for i in table[0].find_all('dd')]
        parsed = {'entity': entity, 'url': url}
        for field, value in zip(fields, vals):
            if field == 'Incorporation Date':
                parsed[field] = value.text.split('(')[0].strip()
            elif field == 'Jurisdiction':
                parsed[field] = ', '.join(value.text.replace('(', '').replace(')', '').split()).strip()
            elif field == 'Registered Address' or field == 'Agent Address':
                joined_addr = ' '.join(value.strings).replace('\n', ', ').replace(',,', ',')
                joined_addr = remove_extra_spaces_commas(joined_addr)
                joined_addr = hax(joined_addr)
                parsed[field] = joined_addr.replace('|', '')

            elif field == 'Directors / Officers' or field == 'Inactive Directors / Officers':
                _officers = [[j.strip().upper() for j in i.text.split(',')] for i in value.find_all('li')]
                parsed[field] = {}
                for row in _officers:
                    if row[0] not in parsed[field]:
                        parsed[field][row[0]] = []
                    parsed[field][row[0]].append(row[1])
                # if 'agent' in value.text:
                #     parsed[field] = value.text.split(', agent')[0].strip()
                # else:
                #     parsed[field] = value.text.strip()
            elif field == 'Registry Page':
                parsed[field] = value.a['href'].strip()
            else:
                parsed[field] = ' '.join(
                    v for v in value.text.strip().split() if v).strip()
        if parsed:
            parsed['path'] = path
            parsed['exit_routing_key'] = kwargs['exit_routing_key']

        parsed = set_arb(parsed, arb)

    except Exception as exc:
        basiclogger.error(exc.__repr__())
    return parsed


def hax(string: str) -> str:
    """
    funky things in the raw data that we fix here
    currently for addresses only..

    d is a dictionary of key-value pairs where:
    key is the (company number) and,
    value is the Registered Address of the Company with that company number

    """
    d = {'(C2237836)': '1840 SOUTHWEST 22ND ST 4TH FL MIAMI FL 33145 United States',
         '(C0168406)': '28 LIBERTY ST NEW YORK NY 10005 United States',
         '(C2713864)': '235 FOSS CREEK CIRCLE HEALDSBURG CA 95448 United States',
         '(C2142832)': '22995 BOUQUET CANYON MISSION VIEJO CA 92692 United States',
         }

    for key in d:
        if key in string:
            string = d[key]
            break
    return string


def remove_extra_spaces_commas(string: str) -> str:
    len_string = len(string)
    while True:
        string = string.strip().strip(',')
        newlen_string = len(string)
        if newlen_string == len_string:
            break
        len_string = newlen_string
    return string