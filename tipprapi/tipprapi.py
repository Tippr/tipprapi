import urllib
import simplejson 

import logging

SETTINGS = {
        'api_url': 'https://marketplace.poweredbytippr.com/api/v0/',
        'api_key': '678563f4bece11e094f4fefd45a4c5ef'
        }

PAGE_SIZE = 5000

logger = logging.getLogger('tippr-api')

class BaseTipprAPIClient(object):
    """
    Client to wrap Tippr API
    """
    def __init__(self, url, apikey):
        if not url:
            raise RuntimeError("url is mandatory")
        if not apikey:
            raise RuntimeError("apikey is mandatory")
        
        self.url = url
        self.apikey = apikey

    def _make_api_request(self, type, resource, params):
        if type == 'get':
            data = self._make_get_request(resource, params)
        else:
            data = self._make_post_request(resource, params)
        
        data = simplejson.loads(data)
        return data

    def _make_get_request(self, resource, params):
        url = self.__base_url(resource) + '&' + urllib.urlencode(params)
        r = urllib.urlopen(url)
        return r.read()

    def _make_post_request(self, resource, params):
        data = urllib.urlencode(params)
        r = urllib.urlopen(self.__base_url(resource), data=data)
        return r.read()
    
    def __base_url(self, resource):
        return self.url + resource + '?' + urllib.urlencode(dict(apikey=self.apikey))

class TipprAPIClient(BaseTipprAPIClient):
    def __init__(self):
        super(TipprAPIClient, self).__init__(SETTINGS['api_url'], SETTINGS['api_key'])

    def find_promotion(self, id):
        return self._make_api_request('get', 'promotion/%(id)s/' % dict(id=id), {})

    def find_promotions(self, query={}):
        return ResultIterator('promotions', lambda params: self._make_api_request('get', 'promotion/', params), query)

    def find_vouchers(self, pid, query={}, **kwargs):
        query = dict(promotion_id=pid)
        return ResultIterator('vouchers', lambda params: self._make_api_request('get', 'voucher/', params), query)

    def return_voucher(self, voucher_id):
        params = dict(action='return')
        result = self._make_api_request('post', 'voucher/%(id)s/action/' % dict(id=voucher_id), params)
        logger.debug('returning voucher %s: %s' % (voucher_id, result))
        return result

    def close_promotion(self, pid):
        result = ''
        try:
            params = dict(action='close')
            result = self._make_api_request('post', 'promotion/%(id)s/action/' % dict(id=pid), params)
            logger.debug('closing promotion %s: %s' % (pid, result))
            if result['new_status'] == "close_delayed":
                result = self._make_api_request('post', 'promotion/%(id)s/action/' % dict(id=pid), params)
        except:
            pass
                
        return result

class ResultIterator(object):
    def __init__(self, key, callback, params):
        self.callback = callback
        self.params = params
        self.page = 0
        self.page_size = PAGE_SIZE
        self.current_result = None
        self.index = 0
        self.page_index = 0
        self.key = key

    def __iter__(self):
        return self

    def next(self):
        if not self.current_result:
            self.__call_api(0)

        if self.index >= self.total:
            raise StopIteration()
        elif self.page_index >= self.page_size:
            self.__call_api(self.page + 1)

        result = self.current_result[self.key][self.page_index]
        self.page_index += 1
        self.index += 1
        return result

    def __call_api(self, page):
        params = dict(page_size = self.page_size, page_start=page)
        params.update(self.params)
        self.current_result = self.callback(params)
        self.total = self.current_result['filtered_count']
        self.page = page
        self.page_index = 0
