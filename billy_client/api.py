from __future__ import unicode_literals
import logging
import urlparse

import requests


class BillyError(RuntimeError):
    """An error for Billy server

    """


class BillyNotFoundError(BillyError):
    """Billy record not found error

    """


class Resource(object):
    """Resource object from the billy server

    """
    def __init__(self, api, json_data):
        self.api = api
        self.json_data = json_data

    def __getattr__(self, key):
        try:
            return self.json_data[key]
        except KeyError:
            return super(Resource. self).__getattre__(key)


class Company(Resource):
    """The company entity object

    """

    def create_customer(self, external_id=None):
        """Create a customer for this company

        """
        url = self.api._url_for('/v1/customers')
        data = {}
        if external_id is not None:
            data['external_id'] = external_id
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('create_customer', resp)
        return Customer(self.api, resp.json())

    def create_plan(self, plan_type, frequency, amount, interval=1):
        """Create a plan for this company

        """
        url = self.api._url_for('/v1/plans')
        data = dict(
            plan_type=plan_type,
            frequency=frequency,
            amount=amount,
            interval=interval,
        )
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('create_plan', resp)
        return Plan(self.api, resp.json())


class Customer(Resource):
    """The customer entity object

    """


class Plan(Resource):
    """The plan entity object

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

    def _auth_args(self):
        return dict(auth=(self.api_key, ''))

    def _check_response(self, method_name, resp):
        """Check response from server, raise error if necessary

        """
        if resp.status_code != requests.codes.ok:
            if resp.status_code == requests.codes.not_found:
                raise BillyNotFoundError(
                    'No such record for {} with code {}, msg{}'
                    .format(method_name, resp.status_code, resp.content)
                )
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
        self.api_key = processor_key
        return Company(self, resp.json())

    def get_company(self, guid):
        """Find a company and return, if no such company exist, 
        BillyNotFoundError will be raised

        """
        url = self._url_for('/v1/companies/{}'.format(guid))
        resp = requests.get(url, **self._auth_args())
        self._check_response('get_company', resp)
        return Company(self, resp.json())
