from __future__ import unicode_literals
import json
import logging
import urlparse

import requests


class BillyError(RuntimeError):
    """An error for Billy server

    """


class Resource(object):
    """Resource object from the billy server

    """
    def __init__(self, json_data):
        self.json_data = json_data

    def __getattr__(self, key):
        try:
            return self.json_data[key]
        except KeyError:
            return super(Resource. self).__getattre__(key)


class Company(Resource):
    """The company entity object

    """


class BillyAPI(object):
    """Billy API is the object provides easy-to-use interface to Billy recurring
    payment system

    """

    DEFAULT_ENDPOINT = 'https://billing.balancedpayments.com'

    def __init__(
        self, 
        api_key,
        endpoint=DEFAULT_ENDPOINT, 
        logger=None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.api_key = api_key
        self.endpoint = endpoint

    def _url_for(self, path):
        """Generate URL for a given path

        """
        return urlparse.urljoin(self.endpoint, path)

    def _check_response(self, method_name, resp):
        """Check response from server, raise error if necessary

        """
        if resp.status_code != requests.codes.ok:
            raise BillyError(
                'Failed to process {} with code {}, msg {}'
                .format(method_name, resp.status_code, resp.content),
                code=resp.status_code,
                msg=resp.content,
            )

    def create_company(self, processor_key):
        """Create a company entity in billy

        """
        url = self._url_for('/v1/companies')
        resp = requests.post(url, data=dict(processor_key=processor_key))
        self._check_response('create_company', resp)
        return Company(resp.json())
