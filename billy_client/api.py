from __future__ import unicode_literals
import logging
import urlparse
import urllib

import requests


class BillyError(RuntimeError):
    """An error for Billy server

    """


class NotFoundError(BillyError):
    """Record not found error

    """


class DuplicateExternalIDError(BillyError):
    """Duplicate external id error

    """


class Resource(object):
    """Resource object from the billy server

    """
    BASE_URI = None

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

    def _list_resources(
        self,
        resource_cls,
        resource_path,
        external_id=None,
        processor_uri=None,
    ):
        """List relative resources under of resource

        """
        assert self.BASE_URI is not None
        kwargs = {}
        if external_id or processor_uri:
            kwargs['extra_query'] = {}
            if external_id:
                kwargs['extra_query']['external_id'] = external_id
            if processor_uri:
                kwargs['extra_query']['processor_uri'] = processor_uri
        return Page(
            api=self.api,
            url=self.api._url_for(
                '{}/{}/{}'.format(self.BASE_URI, self.guid, resource_path)
            ),
            resource_cls=resource_cls,
            **kwargs
        )


class Page(object):
    """Object for iterating over records via API

    """

    def __init__(self, api, url, resource_cls, extra_query=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api = api
        self.url = url
        self.resource_cls = resource_cls
        self.extra_query = extra_query

    def __iter__(self):
        data = self.extra_query.copy() if self.extra_query else {}
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

    BASE_URI = '/v1/companies'

    def create_customer(self, processor_uri=None):
        """Create a customer for this company

        """
        url = self.api._url_for(Customer.BASE_URI)
        data = {}
        if processor_uri is not None:
            data['processor_uri'] = processor_uri
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('create_customer', resp)
        return Customer(self.api, resp.json())

    def create_plan(self, plan_type, frequency, amount, interval=1):
        """Create a plan for this company

        """
        url = self.api._url_for(Plan.BASE_URI)
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

    BASE_URI = '/v1/customers'

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
        funding_instrument_uri=None,
        external_id=None,
        title=None,
        items=None,
        adjustments=None,
        appears_on_statement_as=None,
    ):
        """Create a invoice for this customer

        """
        url = self.api._url_for(Invoice.BASE_URI)
        data = dict(
            customer_guid=self.guid,
            amount=amount,
        )
        if funding_instrument_uri is not None:
            data['funding_instrument_uri'] = funding_instrument_uri
        if title is not None:
            data['title'] = title
        if external_id is not None:
            data['external_id'] = external_id
        if appears_on_statement_as is not None:
            data['appears_on_statement_as'] = appears_on_statement_as
        if items is not None:
            params = self._encode_params('item_', items)
            data.update(params)
        if adjustments is not None:
            params = self._encode_params('adjustment_', adjustments)
            data.update(params)
        resp = requests.post(url, data=data, **self.api._auth_args())
        if resp.status_code == requests.codes.conflict:
            raise DuplicateExternalIDError(
                'Invoice with the same external ID of this customer already exists',
                resp.status_code,
                resp.content,
            )
        self.api._check_response('invoice', resp)
        return Invoice(self.api, resp.json())

    def list_subscriptions(self, external_id=None):
        """List subscriptions

        """
        return self._list_resources(
            resource_cls=Subscription,
            resource_path='subscriptions',
            external_id=external_id,
        )

    def list_invoices(self, external_id=None):
        """List invoices

        """
        return self._list_resources(
            resource_cls=Invoice,
            resource_path='invoices',
            external_id=external_id,
        )

    def list_transactions(self, external_id=None):
        """List transactions

        """
        return self._list_resources(
            resource_cls=Transaction,
            resource_path='transactions',
            external_id=external_id,
        )


class Plan(Resource):
    """The plan entity object

    """
    BASE_URI = '/v1/plans'

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

    #: Debiting type plan
    TYPE_DEBIT = 'debit'
    #: Crediting type plan
    TYPE_CREDIT = 'credit'

    TYPE_ALL = [
        TYPE_DEBIT,
        TYPE_CREDIT,
    ]

    def subscribe(
        self,
        customer_guid,
        funding_instrument_uri=None,
        amount=None,
        started_at=None,
        appears_on_statement_as=None,
    ):
        """Subscribe a customer to this plan

        """
        url = self.api._url_for(Subscription.BASE_URI)
        data = dict(
            plan_guid=self.guid,
            customer_guid=customer_guid,
        )
        if funding_instrument_uri is not None:
            data['funding_instrument_uri'] = funding_instrument_uri
        if amount is not None:
            data['amount'] = amount
        if appears_on_statement_as is not None:
            data['appears_on_statement_as'] = appears_on_statement_as
        if started_at is not None:
            data['started_at'] = started_at.isoformat()
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('subscribe', resp)
        return Subscription(self.api, resp.json())

    def list_customers(self, external_id=None):
        """List customers

        """
        return self._list_resources(
            resource_cls=Customer,
            resource_path='customers',
            external_id=external_id,
        )

    def list_subscriptions(self, external_id=None):
        """List subscriptions

        """
        return self._list_resources(
            resource_cls=Subscription,
            resource_path='subscriptions',
            external_id=external_id,
        )

    def list_invoices(self, external_id=None):
        """List invoices

        """
        return self._list_resources(
            resource_cls=Invoice,
            resource_path='invoices',
            external_id=external_id,
        )

    def list_transactions(self, external_id=None):
        """List transactions

        """
        return self._list_resources(
            resource_cls=Transaction,
            resource_path='transactions',
            external_id=external_id,
        )


class Subscription(Resource):
    """The subscription entity object

    """

    BASE_URI = '/v1/subscriptions'

    def cancel(self):
        """Cancel the subscription

        """
        url = self.api._url_for('{}/{}/cancel'.format(self.BASE_URI, self.guid))
        resp = requests.post(url, **self.api._auth_args())
        self.api._check_response('cancel', resp)
        return Subscription(self.api, resp.json())

    def list_invoices(self, external_id=None):
        """List invoices

        """
        return self._list_resources(
            resource_cls=Invoice,
            resource_path='invoices',
            external_id=external_id,
        )

    def list_transactions(self, external_id=None):
        """List transactions

        """
        return self._list_resources(
            resource_cls=Transaction,
            resource_path='transactions',
            external_id=external_id,
        )


class Invoice(Resource):
    """The invoice entity object

    """

    BASE_URI = '/v1/invoices'

    def refund(self, amount):
        """Issue a refund

        """
        url = self.api._url_for('{}/{}/refund'.format(self.BASE_URI, self.guid))
        data = dict(amount=amount)
        resp = requests.post(url, data=data, **self.api._auth_args())
        self.api._check_response('refund', resp)
        return Subscription(self.api, resp.json())

    def list_transactions(self, external_id=None):
        """List transactions

        """
        return self._list_resources(
            resource_cls=Transaction,
            resource_path='transactions',
            external_id=external_id,
        )


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
                raise NotFoundError(
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
        company = Company(self, resp.json())
        self.api_key = company.api_key
        return company

    def _get_record(self, guid, path_name, method_name):
        url = self._url_for('/v1/{}/{}'.format(path_name, guid))
        resp = requests.get(url, **self._auth_args())
        self._check_response(method_name, resp)
        return Company(self, resp.json())

    def get_company(self, guid):
        """Find a company and return, if no such company exist,
        NotFoundError will be raised

        """
        return self._get_record(
            guid=guid,
            path_name='companies',
            method_name='get_company',
        )

    def get_customer(self, guid):
        """Find a customer and return, if no such customer exist,
        NotFoundError will be raised

        """
        return self._get_record(
            guid=guid,
            path_name='customers',
            method_name='get_customer',
        )

    def list_customers(self, processor_uri=None):
        """List customers

        """
        kwargs = {}
        if processor_uri:
            kwargs['extra_query'] = dict(processor_uri=processor_uri)
        return Page(
            api=self,
            url=self._url_for('/v1/customers'),
            resource_cls=Customer,
            **kwargs
        )

    def get_plan(self, guid):
        """Find a plan and return, if no such plan exist,
        NotFoundError will be raised

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
        NotFoundError will be raised

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
        NotFoundError will be raised

        """
        return self._get_record(
            guid=guid,
            path_name='invoices',
            method_name='get_invoice',
        )

    def list_invoices(self, external_id=None):
        """List invoices

        """
        kwargs = {}
        if external_id:
            kwargs['extra_query'] = dict(external_id=external_id)
        return Page(
            api=self,
            url=self._url_for('/v1/invoices'),
            resource_cls=Invoice,
            **kwargs
        )

    def get_transaction(self, guid):
        """Find a transaction and return, if no such transaction exist,
        NotFoundError will be raised

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
