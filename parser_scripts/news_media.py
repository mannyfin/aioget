# -*- coding: utf-8 -*-
import os
import re
from typing import Union, Tuple

import requests
from fake_useragent import UserAgent
from matplotlib.pyplot import imread
from newspaper import Article

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core import async_filesystem as newsfs
from core.utils import pop_arb_field_if_exists, set_arb
from configs.base.consts import PROJ_ROOT

ua = UserAgent()

kwds = {'en': ["bribery", "corruption", "hostage taking", "kidnapping", "piracy", "counterfeiting",
               "human trafficking", "organized crime", "currency counterfeiting", "illicit trafficking",
               "racketeering", "cybercrime", "hacking", "phishing", "insider trading", "market manipulation",
               "robbery", "environmental crime", "migrant smuggling", "slave labor", "securities fraud",
               "extortion", "sexual exploitation of children", "pedophilia", "money laundering",
               "falsifying information",
               "narcotics", "arms trafficking", "smuggling", "forgery", "price fixing", "cartel formation",
               "antitrust", "terrorism", "terror financing", "fraud", "embezzlement", "theft", "drug trafficking",
               "illegal distribution", "illegal production", "banned medicine", "fake medicine", "war crime",
               "tax evasion", "tax fraud", "drugs", "slavery", "anti-trust"],
        'es': ['terrorismo', 'blanqueo de dinero', 'lavado de dinero', 'crimen financiero',
               'delito financiero', 'narcotráfico', 'corrupción', 'comercio con personas', 'esquema ponzi',
               'evasión fiscal', 'fraude', 'malversación', 'desfalco', 'soborno', 'terrorista', 'contrabando',
               'acusado', 'acusada', 'condenado', 'condenada', 'detenido', 'detenida', 'encarcelado',
               'encarcelada', 'indiciado', 'indiciada', 'demanda judicial']
        }


def filter_adjust_url(url: str) -> str:
    url = re.sub('(https://translate.google.com/.*&u=)', '', url)
    if '&prev=search' in url:
        url = url[:url.index('&prev=search')]
    if '&sa=' in url:
        url = url[:url.index('&sa=')]
    if 'sitemap' in url:
        return ''
    return url


def is_relevant(text: str, language: str) -> bool:
    text = text.lower()
    check_kwds = kwds.get(language, kwds['en'])
    if any(k in text for k in check_kwds):
        return True
    return False


def create_simple_html(url, source, text, ners, collected_date, collected_title, date, top_image, htmltag, language):
    if language == 'es':
        orig_article = '(noticia original)'
        read_orig = 'LEER LA NOTICIA ORIGINAL'
        published = '[publicado]'
        collected = '[colectado]'
    else:
        orig_article = '(original article)'
        read_orig = 'READ THE ORIGINAL ARTICLE'
        published = '[published]'
        collected = '[collected]'
    html = ''
    html += '<!DOCTYPE html>\n'
    html += '<html>\n' if not htmltag else f"{htmltag}\n"
    html += '<body>\n'
    html += '<style>\n'
    html += '  .center {\n'
    html += '    margin: auto;\n'
    html += '    width: 50%;\n'
    html += '    text-align: center;\n'
    html += '    padding: 30px;\n'
    html += '    background-color: white;\n'
    html += '  }\n'
    html += '  .justify {\n'
    html += '    margin: auto;\n'
    html += '    width: 50%;\n'
    html += '    text-align: justify;\n'
    html += '    padding: 40px;\n'
    html += '    background-color: white;\n'
    html += '    color: black;\n'
    html += '  }\n'
    html += '</style>\n'
    html += '<div class="center">\n'
    html += '  <h2>' + collected_title + '</h2>\n'
    html += '  <h4>' + source + '</h4>\n'
    html += f'  <a href="{url}" target="_blank">{orig_article}</a>\n'
    if date == '':
        date = '- '
    try:
        html += f'  <h4>{str(date)}{published} | {str(collected_date)}{collected}</h4>\n'
    except:
        html += '\n'
    html += '  <img src="' + top_image + '" style="width:400px;">\n'
    html += '</div>\n'
    html += '<div class="justify">\n'
    for line in text.split('\n'):
        for ner in ners:
            line = line.replace(ner, '<b>' + ner + '</b>')
        html += '  <p>' + line + '</p>\n'
    html += '</div>\n'
    html += '<div class="center">\n'
    html += f'  <a href="{url}" target="_blank">{read_orig}</a>\n'
    html += '</div>\n'
    html += '</body>\n'
    html += '</html>\n'
    return html


def format_date(date):
    if len(date) == 8:
        date = date[:4] + '-' + date[4:6] + '-' + date[6:]
    return date


def save_topimage(source, date, imgnme, all_images, language):
    try:
        folder = re.sub('\W+', '', date)[:8]
    except:
        folder = 'temp'
    image_path = ''
    for ptopimage in all_images:
        image_path = ''
        try:
            if not ptopimage or ptopimage.strip() == '' or len(ptopimage.strip()) > 256:
                continue
            if ptopimage.startswith('data:'):
                continue
            if ptopimage.startswith('//'):
                ptopimage = ptopimage[2:]
            elif ptopimage.startswith('/'):
                ptopimage = 'https://' + source + ptopimage
            # todo async-ify this code
            response = requests.get(ptopimage, timeout=10)
            # path = f"{PROJ_ROOT}/images/{folder}/"
            if response.status_code == 200:
                if language == 'es':
                    os.makedirs(f"{PROJ_ROOT}/images-es/{folder}/", exist_ok=True)
                else:
                    os.makedirs(f"{PROJ_ROOT}/images/{folder}/", exist_ok=True)

                image_dir = 'images-es' if language == 'es' else 'images'

                image_path = f"{image_dir}/{folder}/" + re.sub('\W+', '', date) + '_' + imgnme.replace('.html', '') \
                    .replace('.htm', '') \
                    .replace('%', '') \
                    .replace('|', '-')
                try:
                    # print(image_path)
                    with open(f"{PROJ_ROOT}/{image_path}", 'wb') as fimg:
                        fimg.write(response.content)
                except Exception as exc:
                    # print(exc.__repr__())
                    continue
                try:
                    w, h, c = imread(f"{PROJ_ROOT}/{image_path}").shape
                    if 200 <= h <= 3000 and 200 <= w <= 3000:
                        break
                    else:
                        os.remove(f"{PROJ_ROOT}/{image_path}")
                        image_path = ''
                except Exception as exc:
                    # print(exc.__repr__())
                    os.remove(f"{PROJ_ROOT}/{image_path}")
                    image_path = ''
        except Exception as exc:
            # print(exc.__repr__())
            image_path = ''
    # if not image_path:
    # print('fdamn')
    # print(image_path)
    return image_path


# def process_url(nrow, url, len_urls):
#     fexists = True
#     phtml = -1
#     with eventlet.Timeout(360):
#         # print('Processing',f)
#         print('Processing url', nrow, 'of', len_urls, url, '...', flush=True)
#         if not newsfs.exists(f'{PROJ_ROOT}/pages', url):
#             idx = date  # '20200218'#datetime.now().strftime('%Y%m%d')
#             title = ''
#             imgurl = ''
#             source = url.split('//')[1].split('/')[0]
#             imgnme = url.split('/')[-1] if url.split('/')[-1] != '' else url.split('/')[-2]
#             phtml, ptitle, pauthors, pdate, pkeywords, ptopimage = parse_link(url, source, idx, title, imgurl, imgnme)
#             # print(phtml,ptitle,pauthors,pdate,pkeywords,ptopimage)
#             fexists = False
#     return (nrow, url, fexists, phtml)


def parse(*args, **kwargs) -> Union[dict, Tuple]:
    """
    This is the snapshot function
    
    Args:
        url: 
        collected_date: 

    Returns:

    """
    response: str = ''
    encoded_url: str = ''
    language = 'en'
    entity_searched = ''
    arb = {}
    if kwargs:
        entity_searched = kwargs['entity']
        url = kwargs['url']
        encoded_url = kwargs['encoded_url'] if 'encoded_url' in kwargs else ''
        collected_date = kwargs['date']
        with open(kwargs['encoded_url'], 'r') as f:
            response = f.read()  # kwargs['response']  # fix to not save the raw article html
        language = kwargs['language'] if 'language' in kwargs else 'en'
        arb, kwargs = pop_arb_field_if_exists(kwargs)

    else:
        url, collected_date = args

    title = ''
    authors = ''
    date = ''
    topimage = ''
    html = ''
    keywords = ''
    collected_title = ''
    collected_image = ''
    # topimage_name = ''
    source = url.split('//')[1].split('/')[0]
    topimage_name = url.split('/')[-1] if url.split('/')[-1] != '' else url.split('/')[-2]

    # lang_class = re.search(r'<html lang="(\w\w)">', response)
    lang_class = re.search(r'<html.*lang="(\w\w)".*>{1}', response)
    # htmltag = lang_class.group(0) if lang_class else ''
    htmltag = f'<html lang="{lang_class.group(1)}">' if lang_class else ''

    if True:
        # Only for article already downloaded
        article = Article(url)
        if response:
            article.set_html(response)
            # todo might need to error handle this
            article.parse()
        elif encoded_url:
            with open(encoded_url) as fin:
                # article = Article(''.join(fin.readlines()))  #
                article.set_html(fin.read())
                # todo might need to error handle this
                article.parse()
        else:
            try:
                article.download()
                article.parse()
            except:
                try:
                    header = {'User-Agent': ua.random}
                    # todo async-ify this code
                    response = requests.get(url, headers=header)
                    article.set_html(response.content)
                    article.parse()
                except:
                    return {}
                    # return html, title, authors, date, keywords, topimage  # ,images
        htmltext = article.html
        # if not is_relevant(htmltext, language):
        #     print('--irrelevant--', url)
        #     return {}
        #     # return html, title, authors, date, keywords, topimage
        # else:
        #     print('--relevant--', url)
        try:
            title = article.title.replace('|', '-')
        except:
            pass
        try:
            keywords = ';'.join([k.replace('|', '-') for k in article.keywords])
        except:
            pass
        try:
            authors = ';'.join([a.replace('|', '-') for a in article.authors])
        except:
            pass
        try:
            date = article.publish_date.strftime("%Y%m%d")
        except:
            pass

        ctext = article.text.replace('|', '-').replace('<br>', ' ')
        if not is_relevant(ctext, language):
            print('--irrelevant--', url)
            return {}
            # return html, title, authors, date, keywords, topimage
        else:
            print('--relevant--', url)
        # save image and article text/info to mongodb

        # try:
        #     if date == '':
        #         folder = re.sub('\W+', '', collected_date)[:8]
        #     else:
        #         folder = re.sub('\W+', '', date)[:8]
        # except:
        #     folder = 'temp'
        # # if language == 'es':
        # #     path = f"{PROJ_ROOT}/pages-es/{folder}/"
        # #     html: str = f"pages-es/{folder}/" + newsfs._decode_filepath(url)
        # #
        # # else:
        # #     path = f"{PROJ_ROOT}/pages/{folder}/"
        # #     html: str = f"pages/{folder}/" + newsfs._decode_filepath(url)
        # #
        # # os.makedirs(path, exist_ok=True)
        #
        # # html: str = f"pages/{folder}/" + newsfs._decode_filepath(url)
        # ners: list = []
        # #        ctext,ners = create_sentiment_text(text)
        # images = list(article.images)
        # if date == '':
        #     topimage = save_topimage(source, collected_date, topimage_name,
        #                              [collected_image, article.top_image] + images[:min(10, len(images))],
        #                              language=language)
        # else:
        #     topimage = save_topimage(source, date, topimage_name,
        #                              [collected_image, article.top_image] + images[:min(10, len(images))],
        #                              language=language)
        #
        # with open(f"{PROJ_ROOT}/{html}", 'w') as fout:
        #     if collected_title == '':
        #         collected_title = title
        #     htext = create_simple_html(url, source, ctext, ners, collected_date, collected_title, format_date(date),
        #                                topimage, htmltag, language)
        #     fout.write(htext)

    if args:
        # older output
        return html, title, authors, date, keywords, topimage  # ,images

    if language == 'en':
        exit_routing_key = 'text'
    else:
        exit_routing_key = f"{language}.{kwargs['exit_routing_key']}"
    output = {'html': html,
              'entity': entity_searched,
              'url': url,
              # 'snapshot': htext,
              'title': title,
              'authors': authors,
              'date': date,
              'keywords': keywords,
              'topimage': topimage,
              'exit_routing_key': exit_routing_key,  # kwargs['exit_routing_key'],
              'client': kwargs['client'],
              'language': language
              }
    output = set_arb(output, arb)
    return output
