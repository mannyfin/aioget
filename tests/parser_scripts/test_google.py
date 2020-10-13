import pytest
import json
from datetime import datetime
import os

from configs.base.consts import PROJ_ROOT
from parser_scripts.google import parse


@pytest.fixture()
def google_results():
    with open(os.path.normpath(f"{PROJ_ROOT}/tests/service/data/r1_google.json"), 'r') as f:
        results = json.load(f)
    return results


def test_parse(google_results):
    today = datetime.today().date().isoformat()
    result = google_results[0]
    parsed_output = parse(**result)
    assert parsed_output == {'entity': 'JOHN DOE',
                             'date': today,
                             'error': '',
                             'language': 'en',
                             'client': 'default',
                             'business_function': 'media',
                             'search_url': 'https://www.google.com/search?safe=strict&q=%22JOHN+DOE%22+AND+%28%22arrested%22+OR+%22money+laundering%22%29+',
                             'urls': ['https://www.justice.gov/usao-ma/pr/john-doe-arrested-passport-fraud',
                                      'https://www.facebook.com/Kennewickpolice/posts/john-doe-arrested-today-officers-responded-to-a-local-business-for-a-male-loiter/2251568751576794/',
                                      'https://www.state.gov/john-doe-arrested-for-passport-fraud/',
                                      'https://www.tampabay.com/news/courts/in-jail-john-doe-inmates-often-identified/2188153/',
                                      'https://www.kbzk.com/news/local-news/john-doe-arrested-after-threatening-bozeman-bar-employees-with-bow-and-arrow',
                                      'https://thisweekinworcester.com/southbridge-john-doe-arrested/',
                                      'https://www.cnn.com/2007/US/law/12/10/court.indicting.dna/index.html',
                                      'https://www.ice.gov/news/releases/update-ice-arrests-john-doe-child-pornography-suspect-rescues-child-ongoing-sexual',
                                      'https://www.smdp.com/john-doe-gets-arrested-and-identified/157179'],
                             'cache_urls': [
                                 'https://webcache.googleusercontent.com/search?q=cache:jdKcIjR4p6AJ:https://www.justice.gov/usao-ma/pr/john-doe-arrested-passport-fraud+&cd=1&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:n8A_JO5guCAJ:https://www.facebook.com/Kennewickpolice/posts/john-doe-arrested-today-officers-responded-to-a-local-business-for-a-male-loiter/2251568751576794/+&cd=2&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:jOtVmHGtnAQJ:https://www.state.gov/john-doe-arrested-for-passport-fraud/+&cd=3&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:dhQvzz5OAY8J:https://www.tampabay.com/news/courts/in-jail-john-doe-inmates-often-identified/2188153/+&cd=4&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:RmBlSGYAzzMJ:https://www.kbzk.com/news/local-news/john-doe-arrested-after-threatening-bozeman-bar-employees-with-bow-and-arrow+&cd=5&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:4r9NmF6ciP4J:https://thisweekinworcester.com/southbridge-john-doe-arrested/+&cd=6&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:DbUbgnKy2IwJ:https://www.cnn.com/2007/US/law/12/10/court.indicting.dna/index.html+&cd=7&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:DbvPF-EquQwJ:https://www.ice.gov/news/releases/update-ice-arrests-john-doe-child-pornography-suspect-rescues-child-ongoing-sexual+&cd=8&hl=en&ct=clnk&gl=us',
                                 'https://webcache.googleusercontent.com/search?q=cache:Qleb8-vJgagJ:https://www.smdp.com/john-doe-gets-arrested-and-identified/157179+&cd=9&hl=en&ct=clnk&gl=us']
                             }
