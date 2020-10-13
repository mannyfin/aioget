from datetime import date
import json
from typing import Optional
import unicodedata
import re

from bs4 import BeautifulSoup
import pandas as pd
from tldextract import tldextract
import pycountry

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger
from core.utils import pop_arb_field_if_exists, set_arb

basiclogger = logger.rabbit_logger(__name__)


def check_panjiva(url):
    urlextract = tldextract.extract(url)
    if 'panjiva' == urlextract.domain:
        return True
    return False


def remove_lang_subdomain(url: str) -> str:
    tld = tldextract.extract(url)
    if tld.subdomain != 'www':
        if 'https://' in url:
            return f"https://{tld.registered_domain}{url[url.index(tld.registered_domain)+len(tld.registered_domain):]}"
    return url


def filter_adjust_url(url: str) -> str:
    # todo remove rows if they do not contain panjiva.com in them...
    # adjust any panjiva urls to show english
    url = re.sub('(https://translate.google.com/.*&u=)', '', url)
    if '&prev=search' in url:
        url = url[:url.index('&prev=search')]
    if '&sa=' in url:
        url = url[:url.index('&sa=')]

    url = re.sub('https://(.*)panjiva*', 'https://panjiva', url)

    if 'sitemap' in url:
        return ''

    if check_panjiva(url):
        return url
    return ''


def parse(**kwargs) -> dict:
    data = {}
    arb, kwargs = pop_arb_field_if_exists(kwargs)

    try:
        url = kwargs['url']
        cache_url = kwargs['cache_url']
        entity_searched = kwargs['entity']
        language = kwargs['client_config']['language'][0]  # english
        sanctioned_jurisdiction_list = kwargs['client_config']['keywords'][language]
        # open file...
        path = kwargs['encoded_url']
        with open(path, 'r') as f:
            resp = f.read()
        # resp = kwargs['response']
        if (url is not None and 'panjiva.com' in url) or (cache_url is not None and 'panjiva.com' in cache_url):
            try:
                data = panjiva_parse_company_info(resp, entity_searched)

            except Exception as exc:
                data = panjiva_parse_shipping_company_info(resp, entity_searched)

        data = check_sanctioned_jurisdiction_affiliation(data, sanctioned_jurisdiction_list)
        if data:
            data['url'] = url if url and 'panjiva.com' in url else cache_url
            data['path'] = path
            data['exit_routing_key'] = kwargs['exit_routing_key']
            data['client'] = kwargs['client']
            data['language'] = language
            data = set_arb(data, arb)
        else:
            data = {}
    except Exception as exc:
        basiclogger.error(exc.__repr__())
    return data


def check_sanctioned_jurisdiction_affiliation(data: dict, sanctioned_jurisdiction: list) -> dict:
    """
    Extract only the Sanctioned Jurisdctions country or shipment country for the entity. If neither found for an
    entity, return an empty dict.

    Args:
        data (dict): data extracted from a panjiva webpage.
        sanctioned_jurisdiction (list): list of sanctioned jurisdictions provided in client config

    Returns:


    # Function to extract the entities with a sanctioned jurisdiction affiliation to merge into a master list
    # ##########This does not cross reference against the entities searched!################
    # :param hashtable: ideally the dictionary saved from the download_webpages function
    # :param sanctioned_jurisdiction: list of sanctioned jurisdictions...
    # :return:


    """
    if not data:
        return {}
    # if isinstance(hashtable, str):
    #     with open(hashtable, 'r') as f:
    #         sjas = json.load(f)
    # elif isinstance(hashtable, dict):
    #     sjas = hashtable
    # else:
    #     raise ValueError('Hashtable must be path to dict (str) or dict')

    sjset = set([sj.upper() for sj in sanctioned_jurisdiction])

    # sjdict = {sj.upper(): sj for sj in sanctioned_jurisdiction}
    ##########################
    for entity, info in data.items():
        if info['company_country'].upper() not in sjset:
            # make it empty since the company country is not a sanctioned jurisdiction
            info['company_country'] = ''
        else:
            info['iso2_company_country'] = [pycountry.countries.search_fuzzy(info['company_country'])[0].alpha_2]
            # if company_key not in affiliations:
            #     affiliations[key] = []
            # affiliations[key].append(element)

        sanc_country_shipments = []
        iso2_country_shipments = []
        if info['country_shipments'] and isinstance(info['country_shipments'], list):
            for country_data in info['country_shipments']:
                if country_data and country_data[0].upper() in sjset:
                    sanc_country_shipments.append(country_data)
                    iso2_country_shipments.append(pycountry.countries.lookup(country_data[1]).alpha_2)
        if sanc_country_shipments or ('iso2_company_country' in info and info['iso2_company_country']):
            info['country_shipments'] = sanc_country_shipments
            info['iso2_country_shipments'] = list(set(iso2_country_shipments))
            return data
        return {}

    ##########################
#     affiliations = {}
#     ct = 0
#     output = []
#     for key, val in sjas.items():
#
#         for element in val:
#             if element['company_country'].lower() in sjset:
#                 if key not in affiliations:
#                     affiliations[key] = []
#                 affiliations[key].append(element)
#                 continue
#             for shipment in element['country_shipments']:
#                 if isinstance(shipment, list) and isinstance(shipment[0], str) and shipment[0].lower() in sjset:
#                     if key not in affiliations:
#                         affiliations[key] = []
#                     affiliations[key].append(element)
#                     break
# #             print(ct)
#         ct += 1
#
#     output = []
#     for key, val in affiliations.items():
#         newval = []
#         shipmentlst = []
#         countries = []
#         urls = []
#         fp = ['']
#         for element in val:
#             if element['company_country'].lower() in sjset:
#                 if key not in newval:
#                     newval.append(key)
#                 if element['company_country'] not in countries:
#                     countries.append(element['company_country'])
#                 if element['url'] not in urls:
#                     urls.append(element['url'])
#                 continue
#             for shipment in element['country_shipments']:
#                 if isinstance(shipment, list) and isinstance(shipment[0], str) and shipment[0].lower() in sjset:
#                     if key not in newval:
#                         newval.append(key)
#                     if shipment[0] not in shipmentlst:
#                         shipmentlst.append(shipment[0])
#                     if element['url'] not in urls:
#                         urls.append(element['url'])
#                     break
#             if newval:
#                 # output.append('|'.join(newval + [','.join(countries)] + [','.join(urls)]))
#                 output.append(newval + [','.join(shipmentlst)] + [','.join(countries)] + [','.join(urls)] + fp)
#     # quick little hack to remove duplicates
#     df = pd.DataFrame(output)
#     df = df.drop_duplicates()
#     out = df.values.tolist()
#     return out


def panjiva_parse_company_info(resp_text: str, entity_searched) -> dict:
    """Panjiva"""
    soup: BeautifulSoup = BeautifulSoup(resp_text, 'lxml')
    entity: Optional[str] = soup.h1.text.strip()

    shipments = soup.find_all('section', class_=lambda tag: tag.startswith('shipment-section') if tag else False)
    dfs: list = []
    hs_codes: list = []
    code_number: list = []
    products: list = []
    country_shipments: list = []
    try:
        company_country = soup.find_all('span',
                                        class_=lambda tag: tag.startswith('profileHeader') if tag else False)
        company_country = company_country[1].text.strip()
    except Exception as exc:
        print('no country found')
        company_country = ''

    for shipment in shipments:
        column_names = [head.text.strip() for head in shipment.find_all('th')]
        table_rows = shipment.find_all('tr')
        table_data = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.strip() for tr in td]
            table_data.append(row)
        #     bugfix, dataframes are not serializeable, therefore convert it to json
        dfs.append(pd.DataFrame(table_data, columns=column_names).to_json())

    address = soup.find('div', class_='container-address').text.strip() if hasattr(
        soup.find('div', class_='container-address'), 'text') else False
    try:
        ols = soup.find_all('ol')
        for ol in ols:
            if 'listHtsCodes' in ol.attrs['class']:
                hs_list = ol.find_all('li')
                hs_codes = []  # text description of hscode
                code_number = []  # hs code number
                for hs_code in hs_list:
                    # "https://stackoverflow.com/questions/51710082/what-does-unicodedata-normalize-do-in-python"
                    item = unicodedata.normalize(u'NFKD', hs_code.a.text.strip()).encode('ascii', 'ignore').decode(
                        'utf8')
                    number = item.split(' -')[0].strip('HS ')
                    code_number.append(int(number) if number.isnumeric() else -1)
                    hs_codes.append(item)
            else:
                prod = ol.find_all('li')
                products = []
                for product in prod:
                    item = unicodedata.normalize(u'NFKD', product.a.text.strip()).encode('ascii', 'ignore').decode(
                        'utf8')
                    products.append(item)

    except Exception as exc:
        try:
            hs = soup.find('ol', class_=lambda tag: tag.endswith('listHtsCodes') if tag else False)
            if hs:
                hs_list = hs.find_all('li')
                hs_codes = []  # text description of hscode
                code_number = []  # hs code number
                for hs_code in hs_list:
                    # "https://stackoverflow.com/questions/51710082/what-does-unicodedata-normalize-do-in-python"
                    item = unicodedata.normalize(u'NFKD', hs_code.a.text.strip()).encode('ascii', 'ignore').decode(
                        'utf8')
                    number = item.split(' -')[0].strip('HS ')
                    code_number.append(int(number) if number.isnumeric() else -1)
                    hs_codes.append(item)
            else:
                hs_codes = []
                code_number = []
        except Exception as exc:
            hs_codes = []
            code_number = []
    try:
        c = soup.find('section', id=lambda tag: tag.startswith('trade-map') if tag else False)
        #             for k, v in json.loads(c.div['data-props'])['choroplethData'].items():
        if c:
            d = json.loads(c.script.string.split('--')[1])
            # since panjiva changes the choropleth key around so much...
            for key in d['data'].keys():
                for k, v in d['data'][key]['countries'].items():
                    country_shipments.append([v['name'], v['iso3'], v['count']])
    except Exception as exc:
        try:
            c = soup.find('section', id=lambda tag: tag.startswith('trade-map') if tag else False)
            #             for k, v in json.loads(c.div['data-props'])['choroplethData'].items():
            if c:
                for k, v in json.loads(c.script.text[4:-3])['data']['country_choropleths']['countries'].items():
                    country_shipments.append([v['name'], v['iso3'], v['count']])
        except Exception as exc:
            try:
                c = soup.find('section', id=lambda tag: tag.startswith('trade-map') if tag else False)
                if c:
                    for k, v in json.loads(c.div['data-props'])['choroplethData'].items():
                        country_shipments.append([v['name'], v['iso3'],  v['count']])
            except Exception as exc:
                country_shipments = [-1]
                basiclogger.error(f'exc in panjiva country shipments: {exc.__repr__()}')

    data = {entity: {'shipments': dfs, 'address': address, 'HS_codes': hs_codes, 'HS_number': code_number,
                     'products': products, 'company_country': company_country, 'country_shipments': country_shipments,
                     'entity_searched': entity_searched, 'date_scraped': date.today().isoformat()
                     },
            'entity': entity,
            }

    return data


def panjiva_parse_shipping_company_info(resp_text: str, entity_searched) -> dict:
    soup = BeautifulSoup(resp_text, 'lxml')
    entity = soup.h1.text.strip()

    # Standard Carrier Alpha Code(SCAC)
    #         scac_code = soup.find('span', class_=lambda tag: 'scac_code' in tag if tag else False).text
    # extract header info and data from each section summary for a shipping company
    summary_header = []
    summary_data = []

    for item in soup.find_all('div', class_='summary-group'):
        summary_header.append(item.h2.text.strip())
        try:
            # good for first section - since this captures the date to-from for the number of shipments.
            summary_data.append(
                [item.ul.li['original-title']] + [int(i.get_text()) if i.get_text().isnumeric() else i.get_text()
                                                  for i in item.ul.li.find_all('div')])
        except Exception as exc:
            try:
                # how many of a particular section. Ex. number of Suppliers
                number = int(item.find('div', class_=lambda tag: tag.startswith(
                    'numbers-customers') if tag else False).span.text)
                vals = []
                for list_item in item.find_all('li'):
                    vals.append([list_item.a['href'], list_item.text.strip()])
                summary_data.append([number, vals])
            except Exception as exc:
                # probably nothing here worth extracting?
                summary_header.pop()
                basiclogger.error(exc.__repr__())
    if len(summary_header) == len(summary_data):
        out = {summary_header[idx]: summary_data[idx] for idx in range(len(summary_header))}
        # self.data = {entity: out}
        data = out
    else:
        data = {summary_header, summary_data}

    data['entity_searched'] = entity_searched
    data = {entity: data, 'entity': entity}
    #         self.data['scac_code'] = scac_code

    return data


