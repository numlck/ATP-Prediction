#!/usr/bin/env python3

import random
import sys

import lxml.html as lh
import requests
import traceback
requests.adapters.DEFAULT_RETRIES = 0

class FreeProxy:

    def __init__(self, country_id=[], timeout=5, rand=False):
        self.country_id = country_id
        self.timeout = timeout
        self.random = rand

    def get_proxy_list(self):
        try:
            page = requests.get('https://www.sslproxies.org')
            doc = lh.fromstring(page.content)
            tr_elements = doc.xpath('//*[@id="proxylisttable"]//tr')
            if not self.country_id:
                proxies = [f'{tr_elements[i][0].text_content()}:{tr_elements[i][1].text_content()}' for i in
                           range(1, 101)]
            else:
                proxies = [f'{tr_elements[i][0].text_content()}:{tr_elements[i][1].text_content()}' for i in
                           range(1, 101)
                           if tr_elements[i][2].text_content() in self.country_id]
            return proxies
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

    def get(self):
        proxy_list = self.get_proxy_list()
        if self.random:
            random.shuffle(proxy_list)
            proxy_list = proxy_list
        working_proxy = None
        try:
            p = self.check_if_proxy_is_working(proxy_list)
            if p:
                working_proxy = p
                return working_proxy
        except requests.exceptions.RequestException:
            pass
   
    def check_if_proxy_is_working(self, proxies):
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry

        import grequests
        session = grequests.Session()
        retry = Retry(connect=0, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        urls = []
        for proxy in proxies:
            px = {
                'http': "http://" + proxy,
            }
            urls.append(grequests.get('http://0.gravatar.com/avatar/c77120cb5dad4e57ec374451d01aec7a?s=150&d=mysteryman&r=G', headers={"p":proxy},proxies=px, timeout=self.timeout, stream=True))
            
        def exception_handler(request, exception):
            pass
            #print("Request failed")
            #print(exception)

        x = grequests.map(set(urls), exception_handler=exception_handler)
        working = []
        for r in x:
            if r:
                if r.status_code == 200:
                    working.append("http://"+r.request.__dict__["headers"]["p"])
        return working