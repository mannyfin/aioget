import pytest
from datetime import datetime
import os
import redis
import json

from core import filtration

from pytest_redis import factories

redis_external = factories.redisdb('redis_nooproc')


def test_my_redis(redis_external):
    """Check that it's actually working on redis database."""
    redis_external.set('test1', 'test')
    redis_external.set('test2', 'test')

    # my_functionality = MyRedisBasedComponent()
    # my_functionality.do_something()
    # assert my_functionality.did_something

    assert redis_external.get("test1") == b'test'


@pytest.fixture()
def entities():
    entities = ["JOHN DOE", "JANE DOE", "NEW GUY", "OLD GUY"]
    return entities


@pytest.fixture()
def url_filter_exclusion_patterns():
    return [
        "facebook.com", "linkedin.com", "twitter.com", "instagram.com", "www.glassdoor.", "www.indeed.",
        "www.britannica.com", "myspace", "youtube.com", "wikipedia", "pinterest", "reddit", "amazon.com",
        "alibaba.com", "github.com", "dictionary.", "wiktionary.org", "www.linguee.", "yelp.com",
        "www.tripadvisor", "soundcloud.com", "www.gettyimages.", "groupdating.club",
        "www.ancestry.com", "https://translate.google.com", "www.ziprecruiter.com", "200.88.114.33",
        "merriam-webster.com", "spotify.com", "prezi.com", "classroom.google.com", "www.espn.com",
        "www.geeksforgeeks.org", "www.quora.com", "support.google.com", "www.airbnb.", "www.expedia.",
        "www.tutorialspoint.com", "moovitapp.com", "mapquest.com", "www.opentable.com", "outlook.live.com",
        "www.carinsuranceguidebook.", "419scam.org", "www.abercrombie.", "www.helpwanted.", "pornhub", "xnxx",
        "playboy", "xvideos.com", "torrent", "porno", "play.google.com", "films", "movies", "boob", "xporn",
        "dirtyporn", "\\.tk", "imgur.com", "www.waitrose.com", "twitch.tv", "celllookups.com", "www.researchgate.net",
        "www.mlb.com", "rstudio.com", "tumblr.com", "\\.gz", "https://scholar.google.com/citations?",
        "www.dreamville.com/", "www.learn-c.org", "www.kaggle.com", "www.cprogramming.com", "www.jcrew.com",
        "r-project.org", "www.apartments.com", "www.imdb.com", "science.sciencemag.org/content", "krecs.com",
        "https://qz.com/1302211/haitch-or-aitch-english-speakers-cant-agree-on-how-to-say-h/",
        "http://dev.stein.cl/sli/apertura/FormDapi.aspx?User=CTAMAYO&IdEjec=CTS", "www.shutterstock.com",
        "https://books.google.com", "quizlet.com", "gsuite.google.com", "www.vocabulary.com",
        "https://sites.google.com/site/hj7cbm27/ConsumerElectronics/etraders", "\\.xls", "\\.xlsx", "\\.pdf", "\\.doc",
        "\\.docx", "\\.jpg", "\\.ppsx", "\\.jpeg", "\\.mp4", "\\.mp3", "ftp://"
    ]


@pytest.mark.parametrize('entity, language, business_function, refresh_period',
                         [('TEST', 'en', 'news', {"days": 0,
                                                  "months": 6,
                                                  "years": 0,
                                                  }
                           ),
                          ('EXIST', 'en', 'news', {"days": 0,
                                                   "months": 6,
                                                   "years": 0,
                                                   }
                           ),
                          ('Repeat', 'en', 'news', {"days": 0,
                                                    "months": 6,
                                                    "years": 0,
                                                    }
                           ),
                          ])
def test_filter_entities_redis(redis_external, entity, language, business_function, refresh_period):
    redis_external.set('EXIST|en|news', json.dumps({'entity': 'EXIST', 'language': language,
                                                    'business_function': business_function,
                                                    'date': datetime.today().date().isoformat()}))
    # very old result that can get re-done
    redis_external.set('REPEAT|en|news', json.dumps({'entity': 'Repeat', 'language': language,
                                                     'business_function': business_function,
                                                     'date': datetime.min.date().isoformat()}))

    result = filtration.filter_entities_redis(entity, language, business_function, refresh_period, redis_external)
    assert result if entity != 'EXIST' else not result


@pytest.mark.parametrize('url', ['https://mysong.mp3', 'https://www.facebook.com/myprofile',
                                 'http://www.newsurl.com/article/date/article-name'])
def test_filter_garbage_url_search_result(url_filter_exclusion_patterns, url):
    if 'news' in url:
        assert filtration.filter_garbage_url_search_result(url, url_filter_exclusion_patterns)
    else:
        assert not filtration.filter_garbage_url_search_result(url, url_filter_exclusion_patterns)


def test_filter_by_date():
    pass


@pytest.mark.parametrize('url, refresh_period', [('http://www.newsurl.com/article/date/article-name', {"days": 0,
                                                                                                     "months": 6,
                                                                                                     "years": 0,
                                                                                                     })])
def test_filter_already_downloaded_url_redis(url, refresh_period, redis_external):
    redis_external.delete(url)
    assert filtration.filter_already_downloaded_url_redis(url, refresh_period, redis_external)
    redis_external.set(url, json.dumps({'url': url, 'success': 0, 'date': datetime.today().date().isoformat()}))

    assert filtration.filter_already_downloaded_url_redis(url, refresh_period, redis_external)
    redis_external.set(url, json.dumps({'url': url, 'success': 1, 'date': datetime.today().date().isoformat()}))
    assert not filtration.filter_already_downloaded_url_redis(url, refresh_period, redis_external)
