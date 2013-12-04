from __future__ import unicode_literals
import logging
import urlparse
import urllib

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

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.json_data)

    def __getattr__(self, key):
        try:
            return self.json_data[key]
        except KeyError:
            return super(Resource. self).__getattre__(key)


class Page(object):
    """Object for iterating over records via API

    """

    def __init__(self, api, url, resource_cls, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api = api
        self.url = url
        self.resource_cls = resource_cls

    def __iter__(self):
        data = {}
        while True:
            self.logger.debug(
                'Page for %s getting %s', 
                self.resource_cls.__name__,
                data,
            )
            query = urllib.urlencode(data)
            url = self.url + '?' + query
            resp = requests.get(url, **self.api._auth_args())
            json_data = resp.json()
            self.logger.debug('Page result %r', json_data)
            # TODO: we should improve the API to make iteration more efficient
            #       add a next_url field or something like that
            if not json_data['items']:
                break
            for item in json_data['items']:
                yield self.resource_cls(self.api, item)
            data['offset'] = json_data['offset'] + json_data['limit']
            data['limit'] = json_data['limit']


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

    def _encode_params(self, prefix, items):
        params = {}
        for i, item in enumerate(items):
            for key, value in item.iteritems():
                param_key = unicode(prefix + '{}{}'.format(key, i))
                params[param_key] = unicode(value)
        return params 

    def invoice(
        self, 
        amount, 
        payment_uri=None,
        title=None, 
        items=None, 
        adjustments=None, 
    ):
        """Create a invoice for this customer 

        """
        url = self.api._url_for('/v1/invoices')
        data = dict(
            customer_guid=self.guid,
            amount=amount,
        )
        if payment_uri is not None:
            data['payment_uri'] = payment_uri 
        if title is not None:
            data['title'] = title 
        if items is not None:
            params = self._encode_params('item_', items)
            data.update(params)
        if adjustments is not None:
            params = self._encode_params('adjustment_', adjustments)
            data.update(params)
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('invoice', resp)
        return Invoice(self.api, resp.json())


class Plan(Resource):
    """The plan entity object

    """
    #: Daily frequency
    FREQ_DAILY = 'daily'
    #: Weekly frequency
    FREQ_WEEKLY = 'weekly'
    #: Monthly frequency
    FREQ_MONTHLY = 'monthly'
    #: Annually frequency
    FREQ_YEARLY = 'yearly'

    FREQ_ALL = [
        FREQ_DAILY,
        FREQ_WEEKLY,
        FREQ_MONTHLY,
        FREQ_YEARLY,
    ]

    #: Charging type plan
    TYPE_CHARGE = 'charge'
    #: Paying out type plan
    TYPE_PAYOUT = 'payout'

    TYPE_ALL = [
        TYPE_CHARGE,
        TYPE_PAYOUT, 
    ]

    def subscribe(
        self, 
        customer_guid, 
        payment_uri=None, 
        amount=None, 
        started_at=None,
    ):
        """Subscribe a customer to this plan

        """
        url = self.api._url_for('/v1/subscriptions')
        data = dict(
            plan_guid=self.guid,
            customer_guid=customer_guid,
        )
        if payment_uri is not None:
            data['payment_uri'] = payment_uri
        if amount is not None:
            data['amount'] = amount 
        if started_at is not None:
            data['started_at'] = started_at.isoformat()
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('subscribe', resp)
        return Subscription(self.api, resp.json())


class Subscription(Resource):
    """The subscription entity object

    """

    def unsubscribe(self, prorated_refund=False, refund_amount=None):
        """Unsubscribe the subscription

        """
        url = self.api._url_for('/v1/subscriptions/{}/cancel'.format(self.guid))
        data = {}
        if prorated_refund:
            data['prorated_refund'] = str(int(prorated_refund))
        if refund_amount:
            data['refund_amount'] = refund_amount
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('unsubscribe', resp)
        return Subscription(self.api, resp.json())


class Invoice(Resource):
    """The invoice entity object

    """


class Transaction(Resource):
    """The transaction entity object

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
                    .format(method_name, resp.status_code, resp.content),
                    resp.status_code,
                    resp.content,
                )
            raise BillyError(
                'Failed to process {} with code {}, msg {}'
                .format(method_name, resp.status_code, resp.content),
                resp.status_code,
                resp.content,
            )

    def create_company(self, processor_key):
        """Create a company entity in billy

        """
        url = self._url_for('/v1/companies')
        resp = requests.post(url, data=dict(processor_key=processor_key))
        self._check_response('create_company', resp)
        self.api_key = processor_key
        return Company(self, resp.json())

    def _get_record(self, guid, path_name, method_name):
        url = self._url_for('/v1/{}/{}'.format(path_name, guid))
        resp = requests.get(url, **self._auth_args())
        self._check_response(method_name, resp)
        return Company(self, resp.json())

    def get_company(self, guid):
        """Find a company and return, if no such company exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='companies',
            method_name='get_company',
        )

    def get_customer(self, guid):
        """Find a customer and return, if no such customer exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='customers',
            method_name='get_customer',
        )

    def list_customers(self):
        """List customers

        """
        return Page(
            api=self, 
            url=self._url_for('/v1/customers'),
            resource_cls=Customer,
        )

    def get_plan(self, guid):
        """Find a plan and return, if no such plan exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='plans',
            method_name='get_plans',
        )

    def list_plans(self):
        """List plans

        """
        return Page(
            api=self, 
            url=self._url_for('/v1/plans'),
            resource_cls=Plan,
        )

    def get_subscription(self, guid):
        """Find a subscription and return, if no such subscription exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='subscriptions',
            method_name='get_subscriptions',
        )

    def list_subscriptions(self):
        """List subscriptions

        """
        return Page(
            api=self, 
            url=self._url_for('/v1/subscriptions'),
            resource_cls=Subscription,
        )

    def get_invoice(self, guid):
        """Find an invoice and return, if no such invoice exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='invoices',
            method_name='get_invoice',
        )

    def list_invoices(self):
        """List invoices

        """
        return Page(
            api=self, 
            url=self._url_for('/v1/invoices'),
            resource_cls=Invoice,
        )

    def get_transaction(self, guid):
        """Find a transaction and return, if no such transaction exist, 
        BillyNotFoundError will be raised

        """
        return self._get_record(
            guid=guid, 
            path_name='transactions',
            method_name='get_transactions',
        )

    def list_transactions(self):
        """List transactions

        """
        return Page(
            api=self, 
            url=self._url_for('/v1/transactions'),
            resource_cls=Transaction,
        )
