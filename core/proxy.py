""" A helper class to include proxies in requests"""

from typing import Optional
# import os
# import sys
# sys.path.insert(0, os.path.abspath('../configs'))

from configs.base import api


class Proxy(object):
    def __init__(self, proxy_kind: Optional[str] = None):
        # self.use_proxy: bool = use_proxy
        # self.CONNECTIONS = 200  # int(200 * 1.15 / self.procs)
        self.PROXY_HOST: str = api.PROXY_HOST
        self.PROXY_PORT: str = api.PROXY_PORT
        # Make sure to include ':' at the end of the api key string
        self.PROXY_AUTH: str = api.CRAWLERA_API[proxy_kind]
        self.PROXIES = {"https": "https://{}@{}:{}/".format(self.PROXY_AUTH, self.PROXY_HOST, self.PROXY_PORT),
                        "http": "http://{}@{}:{}/".format(self.PROXY_AUTH, self.PROXY_HOST, self.PROXY_PORT)}
