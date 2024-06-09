# -*- coding: utf-8 -*-
"""
Created on Tue May 07 00:49:16 2021
@author: maxi7587
"""

import socket
import requests
from requests.adapters import HTTPAdapter, PoolManager


class SourceAddressAdapter(HTTPAdapter):
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super(SourceAddressAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       source_address=self.source_address)


def prepare_sessions(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = requests.session()
    s.mount("http://", SourceAddressAdapter((str(ip), 0)))
    s.mount("https://", SourceAddressAdapter((str(ip), 0)))
    return s


def test(s):
    # print("{}".format(s.get("http://bot.whatismyipaddress.com").text))
    print("{}".format(s.get("https://www.10times.com").text))


if __name__ == "__main__":
    s = prepare_sessions('190.105.232.46')
    test(s)
