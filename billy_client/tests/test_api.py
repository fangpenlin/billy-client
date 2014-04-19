from __future__ import unicode_literals
import unittest
import datetime
import urlparse

import mock

from billy_client import BillyAPI
from billy_client import BillyError
from billy_client import NotFoundError
from billy_client.api import DuplicateExternalIDError
from billy_client.api import Company
from billy_client.api import Customer
from billy_client.api import Plan
from billy_client.api import Invoice
from billy_client.api import Subscription


class TestResource(unittest.TestCase):

    def make_one(self, *args, **kwargs):
        from billy_client.api import Resource
        return Resource(*args, **kwargs)

    def test_resource_to_unicode(self):
        res = self.make_one(None, dict(key='value'))
        self.assertEqual(unicode(res), "<Resource {'key': u'value'}>")

    def test_resource_get_attr(self):
        res = self.make_one(None, dict(key='value'))
        self.assertEqual(res.key, 'value')
        self.assertEqual(res.api, None)
        self.assertEqual(res.json_data, dict(key='value'))

    def test_resource_not_such_attr(self):
        res = self.make_one(None, dict(key='value'))
        with self.assertRaises(AttributeError):
            print(res.no_such_thing)


class TestAPI(unittest.TestCase):

    def make_one(self, *args, **kwargs):
        return BillyAPI(*args, **kwargs)

    @mock.patch('requests.post')
    def test_billy_error(self, post_method):
        mock_company_data = dict(guid='MOCK_COMPANY_GUID')
        post_method.return_value = mock.Mock(
            json=lambda: mock_company_data,
            status_code=503,
            content='Server error',
        )

        api = self.make_one(None, endpoint='http://localhost')
        with self.assertRaises(BillyError):
            api.create_company('MOCK_PROCESSOR_KEY')

    @mock.patch('requests.post')
    def test_create_company(self, post_method):
        mock_company_data = dict(
            guid='MOCK_COMPANY_GUID',
            api_key='MOCK_API_KEY',
        )
        post_method.return_value = mock.Mock(
            json=lambda: mock_company_data,
            status_code=200,
        )

        api = self.make_one(None, endpoint='http://localhost')
        company = api.create_company('MOCK_PROCESSOR_KEY')

        self.assertEqual(company.guid, 'MOCK_COMPANY_GUID')
        self.assertEqual(company.api, api)
        self.assertEqual(company.api.api_key, 'MOCK_API_KEY')
        post_method.assert_called_once_with(
            'http://localhost/v1/companies',
            data=dict(processor_key='MOCK_PROCESSOR_KEY'),
        )

    @mock.patch('requests.get')
    def _test_get_record(self, get_method, method_name, path_name):
        mock_record_data = dict(guid='MOCK_GUID')
        mock_response = mock.Mock(
            json=lambda: mock_record_data,
            status_code=200,
        )
        get_method.return_value = mock_response

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        method = getattr(api, method_name)
        record = method('MOCK_GUID')

        self.assertEqual(record.guid, 'MOCK_GUID')
        self.assertEqual(record.api, api)
        get_method.assert_called_once_with(
            'http://localhost/v1/{}/MOCK_GUID'.format(path_name),
            auth=('MOCK_API_KEY', '')
        )

    @mock.patch('requests.get')
    def _test_get_record_not_found(self, get_method, method_name, path_name):
        mock_record_data = dict(
            guid='MOCK_GUID',
        )
        mock_response = mock.Mock(
            json=lambda: mock_record_data,
            status_code=404,
            content='Not found',
        )
        get_method.return_value = mock_response

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        method = getattr(api, method_name)
        with self.assertRaises(NotFoundError):
            method('MOCK_GUID')

        get_method.assert_called_once_with(
            'http://localhost/v1/{}/MOCK_GUID'.format(path_name),
            auth=('MOCK_API_KEY', '')
        )

    def test_get_company(self):
        self._test_get_record(
            method_name='get_company',
            path_name='companies',
        )

    def test_get_company_not_found(self):
        self._test_get_record_not_found(
            method_name='get_company',
            path_name='companies',
        )

    def test_get_customer(self):
        self._test_get_record(
            method_name='get_customer',
            path_name='customers',
        )

    def test_get_customer_not_found(self):
        self._test_get_record_not_found(
            method_name='get_customer',
            path_name='customers',
        )

    def test_get_plan(self):
        self._test_get_record(
            method_name='get_plan',
            path_name='plans',
        )

    def test_get_plan_not_found(self):
        self._test_get_record_not_found(
            method_name='get_plan',
            path_name='plans',
        )

    def test_get_subscription(self):
        self._test_get_record(
            method_name='get_subscription',
            path_name='subscriptions',
        )

    def test_get_subscription_not_found(self):
        self._test_get_record_not_found(
            method_name='get_subscription',
            path_name='subscriptions',
        )

    def test_get_invoice(self):
        self._test_get_record(
            method_name='get_invoice',
            path_name='invoices',
        )

    def test_get_invoice_not_found(self):
        self._test_get_record_not_found(
            method_name='get_invoice',
            path_name='invoices',
        )

    def test_get_transaction(self):
        self._test_get_record(
            method_name='get_transaction',
            path_name='transactions',
        )

    def test_get_transaction_not_found(self):
        self._test_get_record_not_found(
            method_name='get_transaction',
            path_name='transactions',
        )

    @mock.patch('requests.post')
    def test_create_customer(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        company = Company(api, dict(guid='MOCK_COMPANY_GUID'))
        mock_customer_data = dict(guid='CUMOCK_CUSTOMER')
        mock_response = mock.Mock(
            json=lambda: mock_customer_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        customer = company.create_customer(
            processor_uri='MOCK_BALANCED_CUSTOMER_URI',
        )

        self.assertEqual(customer.guid, 'CUMOCK_CUSTOMER')
        post_method.assert_called_once_with(
            'http://localhost/v1/customers',
            data=dict(processor_uri='MOCK_BALANCED_CUSTOMER_URI'),
            auth=('MOCK_API_KEY', '')
        )

    @mock.patch('requests.post')
    def test_create_plan(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        company = Company(api, dict(guid='MOCK_COMPANY_GUID'))
        mock_plan_data = dict(guid='MOCK_PLAN_GUID')
        mock_response = mock.Mock(
            json=lambda: mock_plan_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        plan = company.create_plan(
            plan_type=Plan.TYPE_DEBIT,
            frequency=Plan.FREQ_DAILY,
            amount='5566',
            interval=123,
        )

        self.assertEqual(plan.guid, 'MOCK_PLAN_GUID')
        post_method.assert_called_once_with(
            'http://localhost/v1/plans',
            data=dict(
                plan_type=Plan.TYPE_DEBIT,
                frequency=Plan.FREQ_DAILY,
                amount='5566',
                interval=123,
            ),
            auth=('MOCK_API_KEY', ''),
        )

    @mock.patch('requests.post')
    def test_subscribe(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))
        plan = Plan(api, dict(guid='MOCK_PLAN_GUID'))
        now = datetime.datetime.utcnow()
        mock_subscription_data = dict(guid='MOCK_SUBSCRIPTION_GUID')
        mock_response = mock.Mock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        subscription = plan.subscribe(
            customer_guid=customer.guid,
            funding_instrument_uri='MOCK_INSTRUMENT_URI',
            amount='5566',
            appears_on_statement_as='hello baby',
            started_at=now,
        )
        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')
       
        post_method.assert_called_once_with(
            'http://localhost/v1/subscriptions',
            data=dict(
                plan_guid='MOCK_PLAN_GUID',
                customer_guid='MOCK_CUSTOMER_GUID',
                funding_instrument_uri='MOCK_INSTRUMENT_URI',
                appears_on_statement_as='hello baby',
                amount='5566',
                started_at=now.isoformat(),
            ),
            auth=('MOCK_API_KEY', ''),
        )

    @mock.patch('requests.post')
    def test_cancel_subscription(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        subscription = Subscription(api, dict(guid='MOCK_SUBSCRIPTION_GUID'))
        mock_subscription_data = dict(
            guid='MOCK_SUBSCRIPTION_GUID',
            canceled=True,
        )
        mock_response = mock.Mock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        subscription = subscription.cancel()

        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')
        self.assertEqual(subscription.canceled, True)
        post_method.assert_called_once_with(
            'http://localhost/v1/subscriptions/{}/cancel'
            .format('MOCK_SUBSCRIPTION_GUID'),
            auth=('MOCK_API_KEY', ''),
        )

    @mock.patch('requests.post')
    def test_invoice(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))
        mock_invoice_data = dict(
            guid='MOCK_INVOICE_GUID',
        )
        mock_response = mock.Mock(
            json=lambda: mock_invoice_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        invoice = customer.invoice(
            amount='5566',
            title='I want you bankrupt invoice',
            funding_instrument_uri='MOCK_INSTRUMENT_URI',
            appears_on_statement_as='hi there',
            items=[
                dict(name='foo', amount=1234),
                dict(type='debit', name='bar', amount=56, quantity=78,
                     volume=90, unit='unit'),
            ],
            adjustments=[
                dict(amount=-100, reason='A Lannister always pays his debts!'),
                dict(amount=20, reason='you owe me'),
            ],
        )

        self.assertEqual(invoice.guid, 'MOCK_INVOICE_GUID')
        post_method.assert_called_once_with(
            'http://localhost/v1/invoices',
            data=dict(
                customer_guid='MOCK_CUSTOMER_GUID',
                funding_instrument_uri='MOCK_INSTRUMENT_URI',
                title='I want you bankrupt invoice',
                appears_on_statement_as='hi there',
                amount='5566',
                # item1
                item_name0='foo',
                item_amount0='1234',
                # item2
                item_type1='debit',
                item_name1='bar',
                item_amount1='56',
                item_quantity1='78',
                item_volume1='90',
                item_unit1='unit',
                # adjustment1
                adjustment_amount0='-100',
                adjustment_reason0='A Lannister always pays his debts!',
                # adjustment2
                adjustment_amount1='20',
                adjustment_reason1='you owe me',
            ),
            auth=('MOCK_API_KEY', ''),
        )

    @mock.patch('requests.post')
    def test_refund_invoice(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        invoice = Invoice(api, dict(guid='MOCK_INVOICE_GUID'))
        mock_invoice_data = dict(guid='MOCK_INVOICE_GUID')
        mock_response = mock.Mock(
            json=lambda: mock_invoice_data,
            status_code=200,
        )
        post_method.return_value = mock_response

        invoice = invoice.refund(amount=999)

        self.assertEqual(invoice.guid, 'MOCK_INVOICE_GUID')
        post_method.assert_called_once_with(
            'http://localhost/v1/invoices/{}/refund'
            .format('MOCK_INVOICE_GUID'),
            data=dict(amount=999),
            auth=('MOCK_API_KEY', ''),
        )

    @mock.patch('requests.post')
    def test_invoice_with_duplicate_external_id(self, post_method):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))
        mock_invoice_data = dict(
            guid='MOCK_INVOICE_GUID',
        )
        mock_response = mock.Mock(
            json=lambda: mock_invoice_data,
            status_code=409,
            content='Duplicate',
        )
        post_method.return_value = mock_response

        with self.assertRaises(DuplicateExternalIDError):
            customer.invoice(
                amount='5566',
                funding_instrument_uri='MOCK_URI',
                external_id='duplaite one',
            )

    @mock.patch('requests.get')
    def _test_list_records(
        self,
        get_method,
        method_name,
        resource_url,
        extra_query=None,
    ):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        result = [
            dict(
                offset=0,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID1'),
                    dict(guid='MOCK_RECORD_GUID2'),
                ],
            ),
            dict(
                offset=2,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID3'),
                    dict(guid='MOCK_RECORD_GUID4'),
                ],
            ),
            dict(
                offset=4,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID5'),
                ],
            ),
            dict(
                offset=6,
                limit=2,
                items=[],
            ),
        ]
        get_method.return_value = mock.Mock(
            json=lambda: result.pop(0),
            status_code=200,
        )

        method = getattr(api, method_name)
        extra_kwargs = extra_query if extra_query is not None else {}
        records = method(**extra_kwargs)

        self.assertEqual(map(lambda r: r.guid, records), [
            'MOCK_RECORD_GUID1',
            'MOCK_RECORD_GUID2',
            'MOCK_RECORD_GUID3',
            'MOCK_RECORD_GUID4',
            'MOCK_RECORD_GUID5',
        ])
        # ensure url
        call_urls = [
            args[0].split('?')[0]
            for args, _ in get_method.call_args_list
        ]
        self.assertEqual(call_urls, [resource_url] * 4)
        # ensure query
        qs_list = []
        for args, _ in get_method.call_args_list:
            o = urlparse.urlparse(args[0])
            query = urlparse.parse_qs(o.query)
            # flatten all values
            for k, v in query.iteritems():
                query[k] = v[0]
            qs_list.append(query)
        expected_querys = [
            dict(),
            dict(offset='2', limit='2'),
            dict(offset='4', limit='2'),
            dict(offset='6', limit='2'),
        ]
        if extra_kwargs:
            for query in expected_querys:
                query.update(extra_kwargs)
        self.assertEqual(qs_list, expected_querys)
        # ensure auth
        call_auths = [kwargs['auth'] for _, kwargs in get_method.call_args_list]
        self.assertEqual([('MOCK_API_KEY', '')] * 4, call_auths)

    @mock.patch('requests.get')
    def _test_list_records_under_resource(
        self,
        get_method,
        resource_cls,
        method_name,
        resource_url,
        extra_query=None,
    ):
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        resource = resource_cls(api, dict(guid='MOCK_RESOURCE_GUID'))
        result = [
            dict(
                offset=0,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID1'),
                    dict(guid='MOCK_RECORD_GUID2'),
                ],
            ),
            dict(
                offset=2,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID3'),
                    dict(guid='MOCK_RECORD_GUID4'),
                ],
            ),
            dict(
                offset=4,
                limit=2,
                items=[
                    dict(guid='MOCK_RECORD_GUID5'),
                ],
            ),
            dict(
                offset=6,
                limit=2,
                items=[],
            ),
        ]
        get_method.return_value = mock.Mock(
            json=lambda: result.pop(0),
            status_code=200,
        )

        method = getattr(resource, method_name)
        extra_kwargs = extra_query if extra_query is not None else {}
        records = method(**extra_kwargs)

        self.assertEqual(map(lambda r: r.guid, records), [
            'MOCK_RECORD_GUID1',
            'MOCK_RECORD_GUID2',
            'MOCK_RECORD_GUID3',
            'MOCK_RECORD_GUID4',
            'MOCK_RECORD_GUID5',
        ])
        # ensure url
        call_urls = [
            args[0].split('?')[0]
            for args, _ in get_method.call_args_list
        ]
        expected_url = resource_url.format('MOCK_RESOURCE_GUID')
        self.assertEqual(call_urls, [expected_url] * 4)
        # ensure query
        qs_list = []
        for args, _ in get_method.call_args_list:
            o = urlparse.urlparse(args[0])
            query = urlparse.parse_qs(o.query)
            # flatten all values
            for k, v in query.iteritems():
                query[k] = v[0]
            qs_list.append(query)
        expected_querys = [
            dict(),
            dict(offset='2', limit='2'),
            dict(offset='4', limit='2'),
            dict(offset='6', limit='2'),
        ]
        if extra_kwargs:
            for query in expected_querys:
                query.update(extra_kwargs)
        self.assertEqual(qs_list, expected_querys)
        # ensure auth
        call_auths = [kwargs['auth'] for _, kwargs in get_method.call_args_list]
        self.assertEqual([('MOCK_API_KEY', '')] * 4, call_auths)

    def test_list_customers(self):
        self._test_list_records(
            method_name='list_customers',
            resource_url='http://localhost/v1/customers',
            extra_query=dict(processor_uri='id'),
        )

    def test_list_plans(self):
        self._test_list_records(
            method_name='list_plans',
            resource_url='http://localhost/v1/plans',
        )

    def test_list_subscriptions(self):
        self._test_list_records(
            method_name='list_subscriptions',
            resource_url='http://localhost/v1/subscriptions',
        )

    def test_list_invoices(self):
        self._test_list_records(
            method_name='list_invoices',
            resource_url='http://localhost/v1/invoices',
            extra_query=dict(external_id='id'),
        )

    def test_list_transactions(self):
        self._test_list_records(
            method_name='list_transactions',
            resource_url='http://localhost/v1/transactions',
        )

    def test_list_plan_customer(self):
        self._test_list_records_under_resource(
            resource_cls=Plan,
            method_name='list_customers',
            resource_url='http://localhost/v1/plans/{}/customers',
        )

    def test_list_plan_subscription(self):
        self._test_list_records_under_resource(
            resource_cls=Plan,
            method_name='list_subscriptions',
            resource_url='http://localhost/v1/plans/{}/subscriptions',
        )

    def test_list_plan_invoice(self):
        self._test_list_records_under_resource(
            resource_cls=Plan,
            method_name='list_invoices',
            resource_url='http://localhost/v1/plans/{}/invoices',
        )

    def test_list_plan_transaction(self):
        self._test_list_records_under_resource(
            resource_cls=Plan,
            method_name='list_transactions',
            resource_url='http://localhost/v1/plans/{}/transactions',
        )

    def test_list_customer_subscription(self):
        self._test_list_records_under_resource(
            resource_cls=Customer,
            method_name='list_subscriptions',
            resource_url='http://localhost/v1/customers/{}/subscriptions',
        )

    def test_list_customer_invoice(self):
        self._test_list_records_under_resource(
            resource_cls=Customer,
            method_name='list_invoices',
            resource_url='http://localhost/v1/customers/{}/invoices',
        )

    def test_list_customer_transaction(self):
        self._test_list_records_under_resource(
            resource_cls=Customer,
            method_name='list_transactions',
            resource_url='http://localhost/v1/customers/{}/transactions',
        )

    def test_list_subscription_invoice(self):
        self._test_list_records_under_resource(
            resource_cls=Subscription,
            method_name='list_invoices',
            resource_url='http://localhost/v1/subscriptions/{}/invoices',
        )

    def test_list_subscription_transaction(self):
        self._test_list_records_under_resource(
            resource_cls=Subscription,
            method_name='list_transactions',
            resource_url='http://localhost/v1/subscriptions/{}/transactions',
        )

    def test_list_invoice_transaction(self):
        self._test_list_records_under_resource(
            resource_cls=Invoice,
            method_name='list_transactions',
            resource_url='http://localhost/v1/invoices/{}/transactions',
        )
