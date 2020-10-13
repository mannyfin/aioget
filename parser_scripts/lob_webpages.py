"""
Extracts the line of business and executive board from B, if available.
data is returned as a dictionary of dictionaries as follows:

{'Entity': {'line_of_business':'companyLOB', 'sector': 'sector', 'industry':'industry',
            'sub_industry':'sub_industry', 'founded':'date founded', 'ADDRESS':'address',
            'phone': phone_num, 'website':web_url, 'num_employees': number_of_employees,
            'management': {'boardMembers': { }, 'totalBoardMembers': numBoardMembers, 'executives':{ },
            'totalExecutives': numExecutives}
            }}

"""
from datetime import datetime, date
from typing import Optional
import re
import os
import json
import copy

from tldextract import tldextract
from bs4 import BeautifulSoup
from polyglot.detect import Detector

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import logger
from core.utils import load_config, pop_arb_field_if_exists, set_arb
from configs.base.consts import PROJ_ROOT, CONFIG_DIR

basiclogger = logger.rabbit_logger(__name__)


def remove_lang_subdomain(url: str) -> str:
    tld = tldextract.extract(url)
    if tld.subdomain != 'www':
        if 'https://' in url:
            return f"https://{tld.registered_domain}{url[url.index(tld.registered_domain) + len(tld.registered_domain):]}"
        return f"http://{tld.registered_domain}{url[url.index(tld.registered_domain) + len(tld.registered_domain):]}"
    return url


def replace_newlines(blurb: str, repl: str = ' - ') -> str:
    return blurb.replace('\r\n', repl).replace('\n', repl)


def filter_adjust_url(url: str) -> str:
    if not any(site in url for site in ['bloomberg.com/profile/company', 'reuters.com/companies/',
                                        'emis.com/php/company-profile']):
        return ''

    url = re.sub('(https://translate.google.com/.*&u=)', '', url)
    if '&prev=search' in url:
        url = url[:url.index('&prev=search')]
    if '&sa=' in url:
        url = url[:url.index('&sa=')]
    if '+&cd=' in url:
        url = url[:url.index('+&cd=')]

    if 'sitemap' in url:
        return ''
    if 'reuters.com' in url:
        url = remove_lang_subdomain(url)
        if url.split('/')[-1] == 'charts':
            url = url.rsplit('/', 1)[0]
    elif 'emis.com' in url:
        if '__en_' not in url and '_en_' not in url[-20:]:
            if '__' in url:
                dunder = url.rindex('__')
                url = url[:dunder] + '__en_' + url[dunder + 5:]
            elif f"_{url.split('/')[-2].lower()}_" in url[-20:]:
                under_lang = url.rindex(f"_{url.split('/')[-2].lower()}_")
                url = url[:under_lang] + '_en_' + url[under_lang + 4:]
    return url


def parse(**kwargs) -> dict:
    """
    resp is the raw response.
    TODO adjust so that I just pass in the soup object
    entity is the one on the page, not the entity_searched
    """
    SVC_CONFIG_PATH: str = f'{CONFIG_DIR}/service/lob.json'
    service_config = load_config(SVC_CONFIG_PATH)
    file_system = f"{PROJ_ROOT}/{service_config['file_system_path']}"


    url = kwargs['url']
    cache_url = kwargs['cache_url']
    entity_searched = [kwargs['entity']]
    # open file...
    with open(kwargs['encoded_url'], 'r') as f:
        resp = f.read()
    # resp = kwargs['response']
    arb, kwargs = pop_arb_field_if_exists(kwargs)

    data: dict = {}

    if not resp:
        basiclogger.debug(f'No response provided from url: {url} cache_url: {cache_url}')
        return data

    if (url is not None and 'bloomberg.com' in url) or (cache_url is not None and 'bloomberg.com' in cache_url):
        data = bloomberg_parse_company_info(resp, entity_searched)
        # bloomberg_get_management_info(resp, soup)

    elif (url is not None and 'emis.com' in url) or (cache_url is not None and 'emis.com' in cache_url):
        data = emis_parse_company_info(resp, entity_searched)

    elif (url is not None and 'reuters.com' in url) or (cache_url is not None and 'reuters.com' in cache_url):
        data = reuters_parse_company_info(resp, entity_searched)

    if not data['line_of_business']:
        basiclogger.debug(f'Nothing parsed from url: {url} cache_url: {cache_url}')
        return {}

    # else:
    #     #             logger.debug('general parse')
    #     #             self.general_parse(resp, url, already_moved=False)
    #
    #     #             entity = self.entity_searched
    #     return data, entity
    lang_route = detect_language(data)
    if lang_route == 'en' or lang_route == 'unknown':
        exit_routing_key = 'lob'
    else:
        exit_routing_key = f"{lang_route}.{kwargs['exit_routing_key']}"

    data['url'] = url
    data['path'] = kwargs['encoded_url']
    data['exit_routing_key'] = exit_routing_key  # kwargs['exit_routing_key']
    data['client'] = kwargs['client']
    data['language'] = kwargs['language']

    # save to fs
    # try:
    #     # if exit_routing_key == 'lob':
    #     # entity_match = re.sub(r'\W+', '', data['entity']).upper()
    #     # datacopy = copy.deepcopy(data)
    #     # fpath = save_record_to_fs(entity_match, record=datacopy, file_system=file_system)
    #     output_msg = {'entity': data['entity'],
    #                   'exit_routing_key': exit_routing_key
    #                   }
    data = set_arb(data, arb)

    # except Exception as exc:
    #     basiclogger.error(exc.__repr__())
    #     data = {}
    return data


# def remove_empty_fields(specific_record: dict) -> dict:
#     """
#     Remove empty fields when SAVING the jsonl file. The general record is defined by the following:
#
#     general_record = {'url1': {specific record 1}, 'url2': {specific record 2} ... }
#
#     specific_record = general_record[url]
#
#     Args:
#         specific_record (dict): the dictionary contained inside a general record
#
#     Returns:
#         specific_record (dict) with the empty entries removed.
#
#     Notes:
#         This does not change the record stored in the LOB DB
#     """
#
#     fields_removed = ['entity_searched', 'client', 'entity_match', 'date_scraped', 'exit_routing_key']
#     unown_num_201 = ['unknown', 'unclassifiable']  # https://www.pokemon.com/us/pokedex/unown
#
#     for key, value in list(specific_record.items()):
#         if key in fields_removed:
#             specific_record.pop(key)
#         elif isinstance(value, int) and value < 0:
#             specific_record.pop(key)
#         elif isinstance(value, (list, dict, tuple)) and not value:
#             specific_record.pop(key)
#         elif isinstance(value, str) and not value.replace('-', ''):
#             specific_record.pop(key)
#         elif isinstance(value, str) and any(k in value.lower() for k in unown_num_201):
#             specific_record.pop(key)
#     # print(json.dumps(specific_record), flush=True)
#     return specific_record


# def save_record_to_fs(entity_match: str, record: dict, file_system: str) -> str:
#     """
#     Removes empty/unnecessary entries and saves the record to the FS as a JSON Lines file
#     Args:
#        file_system:
#        entity_match: Upper-Case normalized entity string.
#        record (dict):
#
#      Returns:
#         None
#     """
#     date_scraped = record['date_scraped'].replace('-', '') \
#         if 'date_scraped' in record else date.today().isoformat().replace('-', '')
#     specific_record = remove_empty_fields(record)
#
#     dirpath = f"{file_system}/{date_scraped}"
#     os.makedirs(dirpath, exist_ok=True)
#     fpath = f"{dirpath}/{entity_match.lower()}.jsonl"
#
#     with open(fpath, 'a') as f:
#         f.write(f"{json.dumps(specific_record)}\n")
#     return fpath


def detect_language(data):
    try:
        text = data["line_of_business"]
        lang = Detector(text)
        det = {i.code: i.confidence for i in lang.languages}
        # sometimes english/spanish isn't the first option, but it is the second option, so we still prefer english
        if lang.language.code == 'en' or 'en' in det:
            return 'en'
        elif lang.language.code == 'es' or 'es' in det:
            return 'es'
        return lang.language.code
    except Exception as exc:
        # possibly not enough text to make estimation. So assume its english
        # and have downstream model take care of errors
        return 'unknown'


def bloomberg_parse_company_info(resp_text: str, entity_searched) -> dict:
    soup = BeautifulSoup(resp_text, 'lxml')
    try:
        entity = soup.find('h1', class_=lambda compName: compName.startswith(
            'companyName') if compName else False).text
    except Exception as exc:
        entity = 'NotFoundonPage'
        basiclogger.error('Entity not found on Bloomberg Page')

    data = {'entity': entity, 'line_of_business': '', 'SECTOR': '', 'INDUSTRY': '',
            'SUB-INDUSTRY': '', 'FOUNDED': '', 'ADDRESS': '',
            'PHONE': '', 'WEBSITE': '', 'NO. OF EMPLOYEES': -1,
            'boardMembers': (), 'executives': (),
            'entity_searched': entity_searched,
            'date_scraped': date.today().isoformat()
            }

    # todo here's an edge case: https://www.bloomberg.com/profile/person/16640228
    compprof = soup.find('section', class_=lambda cpo: cpo.startswith('companyProfileOverview') if cpo else False)

    # add these direct to dictionary, don't call .text in case it returns none
    try:
        # company_name compprof.find('h1').text
        # company line of business
        if compprof:
            business_description = compprof.find('div', class_=lambda desc: desc.startswith(
                'description') if desc else False)
            if business_description and hasattr(business_description, 'text'):
                data['line_of_business'] = replace_newlines(business_description.text)
    except AttributeError as exc:
        basiclogger.error(exc)
        pass
    finally:
        pass
    # might get bugs here...
    try:
        if compprof:
            table_data = compprof.find_all(
                'section', class_=lambda info: info.startswith('infoTableItem'))
            if table_data:
                for entry in table_data:
                    k, v = [i.text for i in entry.children if hasattr(i, 'text')]
                    if k == 'FOUNDED':
                        if len(v) > 1 and v[0].isnumeric():
                            try:
                                # datetime objects are not serializable, but the isoformat is!
                                v = datetime.strptime(v, '%m/%d/%Y').date().isoformat()
                            except Exception:
                                v = ''
                    if k == 'NO. OF EMPLOYEES':
                        if v.isnumeric():
                            v = int(v)
                        else:
                            v = -1
                    data[k] = replace_newlines(v) if isinstance(v, str) else v
    except Exception as exc:
        basiclogger.warning(exc)

    data = bloomberg_get_management_info(soup, data)
    return data


def bloomberg_get_management_info(soup, data):
    #         pass
    # if isinstance(resp_text, bytes):
    #     resp_text = resp_text.decode()
    # # this makes another request for the JSON data
    # bbid = resp_text[resp_text.find('bbid%22%3A%22') + len('bbid%22%3A%22'): resp_text.find('%22', resp_text.find(
    #     'bbid%22%3A%22') + len('bbid%22%3A%22'))]
    if soup.select('div[class*="bodyWrap"]'):
        try:
            if soup.find_all('div', class_=lambda i: i.startswith('executivesContainer') if i else False):
                data['executives'] = tuple([
                    [i.previous.find('div', class_=lambda i: i.startswith('title')).text, i.text] for i in
                    soup.find_all('div', class_=lambda i: i.startswith('executivesContainer') if i else False)[
                        0].find_all('div', {'data-resource-type': 'Person'})])
            if soup.find_all('div', class_=lambda i: i.startswith('boardContainer') if i else False):
                data['boardMembers'] = tuple([i.text for i in
                                              soup.find_all('div',
                                                            class_=lambda i: i.startswith('boardContainer')
                                                            if i else False)[0]
                                             .find_all('div', {'data-resource-type': 'Person'})])
        except Exception as exc:
            pass
    return data


def emis_parse_company_info(resp_text: str, entity_searched) -> dict:
    """EMIS"""

    def get_outer_text(parent) -> str:
        """
        Helpful function found here:
        https://stackoverflow.com/questions/30159020/get-text-of-html-tags-without-text-of-inner-child-tags
        :param parent:
        :return:
        """
        return ''.join(parent.find_all(text=True, recursive=False)).strip()

    soup: BeautifulSoup = BeautifulSoup(resp_text, 'lxml')
    top_info = soup.find('div', class_=lambda tag: tag.startswith('cp-div-info') if tag else False)

    alias = top_info.find('h1').get_text().strip().replace('  ', '').replace('\n', '')
    industry = top_info.find('div', class_=lambda tag: tag.startswith('main-activities') if tag else False).span \
        .next_sibling.strip()

    entity, profile_updated = [i.span.next_sibling.strip(': ')
                               for i in top_info.find_all('span', class_=lambda tag: tag.startswith('cp-info') if tag
        else False)]
    try:
        # datetime is not serializable, but isoformat is!
        profile_updated = datetime.strptime(profile_updated, '%B %d, %Y').date().isoformat()
    except Exception as exc:
        pass
    # about_info = soup.find('div', class_=lambda tag: tag.startswith('cp-info-item') if tag else False)

    company_blurb = soup.find('p').text if hasattr(soup.find('p'), 'text') else ''
    if company_blurb:
        company_blurb = replace_newlines(company_blurb)

    contact_info = soup.find('div', class_=lambda tag: tag.startswith('contact-info') if tag else False)
    outer = contact_info.find_all('p')[0]

    address = get_outer_text(outer).replace('\n', ' ').replace(';', ' ').replace('  ', ' ').replace('  ', '')
    website = contact_info.a.text if hasattr(contact_info.a, 'text') else False

    data = {'entity': entity, 'line_of_business': company_blurb, 'INDUSTRY': industry, 'alias': alias,
            'profile_last_updated': profile_updated, 'ADDRESS': address, 'website': website,
            'entity_searched': entity_searched, 'date_scraped': date.today().isoformat()
            }
    return data


def reuters_parse_company_info(resp_text: str, entity_searched) -> dict:
    """Reuters"""

    soup: BeautifulSoup = BeautifulSoup(resp_text, 'lxml')
    if hasattr(soup.h1, 'text'):
        entity: Optional[str] = soup.h1.text.strip()
    else:
        entity = None
    ticker: Optional[str] = soup.h1.next_sibling.text.strip()
    try:
        company_blurb = soup.find('div',
                                  class_=lambda tag: tag.startswith('Profile-about') if tag else False).p.text
        if company_blurb:
            company_blurb = replace_newlines(company_blurb)
    except Exception as exc:
        company_blurb = ''
    try:
        industry = soup.find('div', class_=lambda tag: 'industry' in tag if tag else False).find_all('p')[-1].text
    except Exception as exc:
        industry = ''
    try:
        address = soup.find('div', class_=lambda tag: 'About-address' in tag if tag else False).text.strip()
        address = address.replace('\r\n', ' ').replace('\n', ' ').replace('  ', ' ')
    except Exception as exc:
        address = ''
    try:
        phone = soup.find('p', class_=lambda tag: 'About-phone' in tag if tag else False).text
    except Exception as exc:
        phone = ''
    try:
        website = soup.find('a', class_=lambda tag: 'website' in tag if tag else False).text
    except Exception as exc:
        website = ''
    try:
        officers = []
        for officer in soup.find_all('div', class_=lambda tag: 'About-officer' in tag if tag else False):
            officers.append(
                tuple([officer.find('p', class_=lambda tag: 'About-officer-name' in tag if tag else False).text.strip(),
                       officer.find('p', class_=lambda tag: 'About-officer-title' in tag
                       if tag else False).text.strip()]))

    except Exception as exc:
        officers = []

    data = {'entity': entity, 'line_of_business': company_blurb,
            'INDUSTRY': industry, 'ADDRESS': address,
            'phone': phone, 'website': website, 'ticker': ticker, 'officers': tuple(officers),
            'entity_searched': entity_searched, 'date_scraped': date.today().isoformat()
            }
    return data
