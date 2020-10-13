import pytest
import json
from datetime import datetime
import os
from configs.base.consts import PROJ_ROOT
import sys
from parser_scripts.googlenews import parse


@pytest.fixture()
def google_news_results():
    with open(os.path.normpath(f"{PROJ_ROOT}/tests/service/data/r2_googlenews.json"), 'r') as f:
        results = json.load(f)
    return results


def test_parse(google_news_results):
    today = datetime.today().date().isoformat()
    result = google_news_results[0]
    parsed_output = parse(**result)
    assert parsed_output == {'entity': 'JANE DOE',
                             'date': today,
                             'language': 'es',
                             'client': 'default',
                             'business_function': 'media',
                             'urls': [],
                             'cache_urls': [],
                             'search_url': 'https://news.google.com/search?q=%22JANE+DOE%22+%22arrested%22++%20-excluded&hl=es-419&gl=US&ceid=US:es-419',
                             'error': ''
                             }
