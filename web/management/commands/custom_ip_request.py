# coding=utf-8
"""
Created on Tue May 07 00:49:16 2021
@author: maxi7587
"""

import socket
import random

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


def get(url, **kwargs):
    ips = [
        # '0.0.0.0',

        # prod IPs
        '190.105.232.46',
        '190.105.232.47',
        '190.105.232.48',
        '190.105.232.49',

        # following IPs down work anymore
        # '190.105.232.50',
        # '190.105.232.51'
    ]
    ip_index = random.randint(0, len(ips) - 1)
    ip = ips[ip_index]
    # s = prepare_sessions('0.0.0.0')
    print('using IP ---> ' + ip)
    s = prepare_sessions(ip)
    return s.get(url, **kwargs)
