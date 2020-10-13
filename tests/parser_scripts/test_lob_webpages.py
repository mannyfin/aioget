import pytest
from pathlib import Path

from parser_scripts import lob_webpages

keys = ['entity',
        'line_of_business',
        'SECTOR',
        'INDUSTRY',
        'SUB-INDUSTRY',
        'FOUNDED',
        'ADDRESS',
        'PHONE',
        'WEBSITE',
        'NO. OF EMPLOYEES',
        'boardMembers',
        'executives',
        'entity_searched',
        'date_scraped',
        'url',
        'path',
        'exit_routing_key',
        'client',
        'language']


@pytest.mark.parametrize('url',
                         ['https://not_an_lob_site.com/',
                          'https://www.emis.com/php/company-profile/EC'
                          '/Productora_Ecuatoriana_de_Frutas_y_Procesados_Diamondfruits_CL_en_5466142.html',
                          'https://www.emis.com/php/company-profile/UA/Elektronmash_PAT__%D0%95%D0%BB%D0%B5%D0%BA%D1'
                          '%82%D1%80%D0%BE%D0%BD%D0%BC%D0%B0%D1%88_%D0%9F%D0%90%D0%A2__ru_3541304.html',
                          ])
def test_filter_adjust_url(url):
    fixed_url = lob_webpages.filter_adjust_url(url)
    if 'emis.com' in fixed_url:
        if '__ru_' in url:
            assert '__ru_' not in fixed_url
        elif '_en_' in url:
            assert url == fixed_url
    elif 'not_an_lob' in url:
        assert not fixed_url


@pytest.mark.parametrize('path', ['data/https_IIwww.bloomberg.comIprofileIcompanyI0457779d_us.html'])
def test_parse(path):
    if Path.cwd().stem == 'tests':
        path = Path.cwd().joinpath(f'parser_scripts/{path}')

    msg = {'url': path.stem.replace('I', '/').replace('_', ':'),
           'cache_url': '',
           'entity': 'TEST ENTTIY',
           'client': 'default',
           'exit_routing_key': 'lob',
           'language': 'en',
           'encoded_url': path.__str__()}
    result = lob_webpages.parse(**msg)
    #ensure mandatory keys are present, even if there are arbitrary extra keys.
    assert all(k in result for k in keys)
    # ensure that all keys that have string values do not have '\n', newlines can exist in arb extra keys.
    assert all('\n' not in result[k] for k in keys if isinstance(result[k], str))
