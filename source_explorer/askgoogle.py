import os
import pickle
import time

import requests

key = 'YOUR_GOOGLE_API_KEY'


class AskGoogle():
    def __init__(self, cachePath):
        self.cachePath = cachePath
        if os.path.isfile(cachePath):
            self.queryCache = pickle.load(open(cachePath, "rb"))
            print("Loading Google ISBN query cache...")
            good = sum([self.queryCache[i] != '' for i in self.queryCache])
            print("Have " + str(good) + " non-empty entries out of " + str(len(self.queryCache)))
        else:
            self.queryCache = {}
    
    def waitAndAskAgain(self, url, params, wait):
        print("WARNING: Got 429, waiting " + str(wait) + " s. and retrying.")
        time.sleep(wait)
        resp = requests.get(url, params=params)
        if resp.status_code == 429 and wait < 32:
            resp = self.waitAndAskAgain(url, params, wait * 2)
        return resp
    
    def askGoogleForISBN(self, title, author):
        if ':' in title:
            title = title.split(':')[0]
        query = 'intitle:"' + title + '"'
        if author != '':
            query = query + '+inauthor:' + author
        if query in self.queryCache:
            # print("ISBN from cache")
            return self.queryCache[query]
        isbn = ''
        params = 'q=' + query + '&key=' + key
        url = 'https://www.googleapis.com/books/v1/volumes'
        resp = requests.get(url, params=params)
        if resp.status_code == 429:
            resp = self.waitAndAskAgain(url, params, 1)
        if resp.status_code != 200:
            print("WARNING: non-200 API response: " + str(resp.status_code))
            return ''
        response = resp.json()
        results = response['totalItems']
        if results == 1:
            item = response['items'][0]
            if 'volumeInfo' in item and 'industryIdentifiers' in item['volumeInfo']:
                for ids in item['volumeInfo']['industryIdentifiers']:
                    if ids['type'] == 'ISBN_13':
                        isbn = ids['identifier']
        self.queryCache[query] = isbn
        if len(self.queryCache) % 100 == 0:
            print("Writing down query cache.")
            pickle.dump(self.queryCache, open(self.cachePath, "wb"))
        return isbn
