from datetime import datetime
import json
import re
from typing import Optional

from dateutil.relativedelta import relativedelta


# todo might want to rename some of the filter_funcs to is_func since they are returning bools.


def filter_entities_redis(entity, language, business_function, refresh_period: dict, master_search_history) -> bool:
    """
    Take an entity, language, and business_function combination and check if it was searched in a Redis DB. If not,
    return the entity and do the search. If it was, then check if searched within refresh period. If searched within
    refresh period, don't do the search. Only do the search if older than the refresh period.

    Args:
        entity:
        language:
        business_function:
        refresh_period:
        master_search_history: Redis DB host - localhost, port = 6379, db=0

    Returns:
        True if the search should be performed
        False otherwise.
    """

    # master_search_history = redis.Redis(**db_params)  # DB from service config
    regexp_entity = re.sub('\W+', '', entity).upper()

    lookup = master_search_history.get(f"{regexp_entity}|{language}|{business_function}")
    if not lookup:
        return True

    # extract out the date (might be just bytestring, or dictionary)
    entity_info = json.loads(lookup)
    if 'date' not in entity_info:
        return True

    date_last_searched = entity_info['date']
    return filter_by_date(date_last_searched, refresh_period)


def filter_garbage_url_search_result(url, url_filter_exclusion_patterns: Optional[list] = None) -> bool:
    """If any of the url_filter_exclusion_patterns appear, then don't bother with it..."""
    if not url_filter_exclusion_patterns:
        return True
    if any(re.findall(pattern, url) for pattern in url_filter_exclusion_patterns):
        return False
    return True


def filter_by_date(date_last_searched, refresh_period: dict) -> bool:
    date_last_searched_datetime = datetime.strptime(date_last_searched, '%Y-%m-%d').date()

    day_period = refresh_period['days']
    month_period = refresh_period['months']
    year_period = refresh_period['years']

    past_date = datetime.today().date() + relativedelta(days=-day_period, months=-month_period, years=-year_period)
    if past_date > date_last_searched_datetime:
        # past_date is newer, so search again
        return True
    return False


def filter_already_downloaded_url_redis(url, refresh_period: dict, master_download_history) -> bool:
    # master_search_history = redis.Redis(**db_params)  # DB from service config

    lookup = master_download_history.get(f"{url}")

    if not lookup:
        return True

    lookup = json.loads(lookup)
    if not lookup['success']:
        return True

    date_last_searched = lookup['date']
    return filter_by_date(date_last_searched, refresh_period)

