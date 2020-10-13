import pytest
from core.proxy import Proxy


@pytest.mark.parametrize('proxy_kind', ['account_name', None, 'hi'])
def test_proxy(proxy_kind):
    if proxy_kind not in ['account_name']:
        with pytest.raises(KeyError) as exc:
            raise Proxy(proxy_kind)
    else:
        proxy = Proxy(proxy_kind)
        assert hasattr(proxy, 'PROXIES')
