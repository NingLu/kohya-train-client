class ApiEndpoint:
    def __init__(self):
        self._api_endpoint_url = ''
        self._api_key = ''

    @property
    def api_endpoint_url(self):
        return self._api_endpoint_url

    @api_endpoint_url.setter
    def api_endpoint_url(self, url):
        if isinstance(url, str):
            self._api_endpoint_url = url
        else:
            raise ValueError("api_endpoint_url must be a string")

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, key):
        if isinstance(key, str):
            self._api_key = key
        else:
            raise ValueError("api_key must be a string")
