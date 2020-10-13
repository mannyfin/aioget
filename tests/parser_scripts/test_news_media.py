import pytest

from parser_scripts import news_media as media


@pytest.mark.parametrize('text,lang', [('money laundering', 'en'),
                                       ('laundering money', 'en')])
def test_is_relevant(text, lang):
    kwds = media.kwds
    result = media.is_relevant(text=text, language=lang)
    for kwd in kwds[lang]:
        if kwd in text:
            assert result
            break
    else:
        assert not result
