from __future__ import unicode_literals
import unittest

from flexmock import flexmock


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
        from billy_client import BillyAPI
        return BillyAPI(*args, **kwargs)

    def test_billy_error(self):
        import requests
        from billy_client import BillyError

        mock_company_data = dict(
            guid='MOCK_COMPANY_GUID',
        )

        mock_response = flexmock(
            json=lambda: mock_company_data,
            status_code=503,
            content='Server error',
        )

        (
            flexmock(requests)
            .should_receive('post')
            .replace_with(lambda url, data: mock_response)
        )

        api = self.make_one(None, endpoint='http://localhost')
        with self.assertRaises(BillyError):
            api.create_company('MOCK_PROCESSOR_KEY')

    def test_create_company(self):
        import requests

        mock_company_data = dict(
            guid='MOCK_COMPANY_GUID',
        )

        mock_response = flexmock(
            json=lambda: mock_company_data,
            status_code=200,
        )

        (
            flexmock(requests)
            .should_receive('post')
            .with_args('http://localhost/v1/companies', 
                       data=dict(processor_key='MOCK_PROCESSOR_KEY'))
            .replace_with(lambda url, data: mock_response)
            .once()
        )

        api = self.make_one(None, endpoint='http://localhost')
        company = api.create_company('MOCK_PROCESSOR_KEY')
        self.assertEqual(company.guid, 'MOCK_COMPANY_GUID')
        self.assertEqual(company.api, api)

    def _test_get_record(self, method_name, path_name):
        import requests

        mock_record_data = dict(
            guid='MOCK_GUID',
        )

        mock_response = flexmock(
            json=lambda: mock_record_data,
            status_code=200,
        )

        (
            flexmock(requests)
            .should_receive('get')
            .with_args('http://localhost/v1/{}/MOCK_GUID'.format(path_name), 
                       auth=('MOCK_API_KEY', ''))
            .replace_with(lambda url, auth: mock_response)
            .once()
        )

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        method = getattr(api, method_name)
        record = method('MOCK_GUID')
        self.assertEqual(record.guid, 'MOCK_GUID')
        self.assertEqual(record.api, api)

    def _test_get_record_not_found(self, method_name, path_name):
        import requests
        from billy_client import NotFoundError

        mock_record_data = dict(
            guid='MOCK_GUID',
        )

        mock_response = flexmock(
            json=lambda: mock_record_data,
            status_code=404,
            content='Not found',
        )

        (
            flexmock(requests)
            .should_receive('get')
            .with_args('http://localhost/v1/{}/MOCK_GUID'.format(path_name), 
                       auth=('MOCK_API_KEY', ''))
            .replace_with(lambda url, auth: mock_response)
            .once()
        )

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        method = getattr(api, method_name)
        with self.assertRaises(NotFoundError):
            method('MOCK_GUID')

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

    def test_create_customer(self):
        import requests
        from billy_client.api import Company
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        company = Company(api, dict(guid='MOCK_COMPANY_GUID'))

        mock_customer_data = dict(
            guid='CUMOCK_CUSTOMER',
        )

        mock_response = flexmock(
            json=lambda: mock_customer_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args('http://localhost/v1/customers', 
                       data=dict(external_id='MOCK_BALANCED_CUSTOMER_URI'),
                       auth=('MOCK_API_KEY', ''))
            .replace_with(mock_post)
            .once()
        )

        customer = company.create_customer(
            external_id='MOCK_BALANCED_CUSTOMER_URI',
        )
        self.assertEqual(customer.guid, 'CUMOCK_CUSTOMER')
        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(external_id='MOCK_BALANCED_CUSTOMER_URI'))

    def test_create_plan(self):
        import requests
        from billy_client.api import Company
        from billy_client.api import Plan
        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        company = Company(api, dict(guid='MOCK_COMPANY_GUID'))

        mock_plan_data = dict(
            guid='MOCK_PLAN_GUID',
        )
        mock_response = flexmock(
            json=lambda: mock_plan_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/plans', 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(
                    plan_type=Plan.TYPE_CHARGE,
                    frequency=Plan.FREQ_DAILY,
                    amount='55.66',
                    interval=123,
                ),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        plan = company.create_plan(
            plan_type=Plan.TYPE_CHARGE,
            frequency=Plan.FREQ_DAILY,
            amount='55.66',
            interval=123,
        )
        self.assertEqual(plan.guid, 'MOCK_PLAN_GUID')

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(
            plan_type=Plan.TYPE_CHARGE,
            frequency=Plan.FREQ_DAILY,
            amount='55.66',
            interval=123,
        ))

    def test_subscribe(self):
        import datetime
        import requests
        from billy_client.api import Plan
        from billy_client.api import Customer

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))
        plan = Plan(api, dict(guid='MOCK_PLAN_GUID'))
        now = datetime.datetime.utcnow()

        mock_subscription_data = dict(
            guid='MOCK_SUBSCRIPTION_GUID',
        )
        mock_response = flexmock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/subscriptions', 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(
                    plan_guid='MOCK_PLAN_GUID',
                    customer_guid='MOCK_CUSTOMER_GUID',
                    payment_uri='MOCK_PAYMENT_URI',
                    amount='55.66',
                    started_at=now.isoformat(),
                ),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        subscription = plan.subscribe(
            customer_guid=customer.guid,
            payment_uri='MOCK_PAYMENT_URI',
            amount='55.66',
            started_at=now,
        )
        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(
            plan_guid='MOCK_PLAN_GUID',
            customer_guid='MOCK_CUSTOMER_GUID',
            payment_uri='MOCK_PAYMENT_URI',
            amount='55.66',
            started_at=now.isoformat(),
        ))

    def test_unsubscribe(self):
        import requests
        from billy_client.api import Subscription

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        subscription = Subscription(api, dict(guid='MOCK_SUBSCRIPTION_GUID'))

        mock_subscription_data = dict(
            guid='MOCK_SUBSCRIPTION_GUID',
            canceled=True,
        )
        mock_response = flexmock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/subscriptions/{}/cancel'
                .format('MOCK_SUBSCRIPTION_GUID'), 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        subscription = subscription.unsubscribe()
        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')
        self.assertEqual(subscription.canceled, True)

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict())

    def test_unsubscribe_with_prorated_refund(self):
        import requests
        from billy_client.api import Subscription

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        subscription = Subscription(api, dict(guid='MOCK_SUBSCRIPTION_GUID'))

        mock_subscription_data = dict(
            guid='MOCK_SUBSCRIPTION_GUID',
            canceled=True,
        )
        mock_response = flexmock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/subscriptions/{}/cancel'
                .format('MOCK_SUBSCRIPTION_GUID'), 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(prorated_refund='1'),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        subscription = subscription.unsubscribe(prorated_refund=True)
        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')
        self.assertEqual(subscription.canceled, True)

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(prorated_refund='1'))

    def test_unsubscribe_with_refund_amount(self):
        import requests
        from billy_client.api import Subscription

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        subscription = Subscription(api, dict(guid='MOCK_SUBSCRIPTION_GUID'))

        mock_subscription_data = dict(
            guid='MOCK_SUBSCRIPTION_GUID',
            canceled=True,
        )
        mock_response = flexmock(
            json=lambda: mock_subscription_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/subscriptions/{}/cancel'
                .format('MOCK_SUBSCRIPTION_GUID'), 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(refund_amount='123'),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        subscription = subscription.unsubscribe(refund_amount='123')
        self.assertEqual(subscription.guid, 'MOCK_SUBSCRIPTION_GUID')
        self.assertEqual(subscription.canceled, True)

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(refund_amount='123'))

    def test_invoice(self):
        import requests
        from billy_client.api import Customer

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))

        mock_invoice_data = dict(
            guid='MOCK_INVOICE_GUID',
        )
        mock_response = flexmock(
            json=lambda: mock_invoice_data,
            status_code=200,
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/invoices', 
                # TODO: oddly... the data here is not compared
                # you can modify data keys and values and it won't fail
                # a bug of flexmock?
                data=dict(
                    customer_guid='MOCK_CUSTOMER_GUID',
                    amount='5566',
                    items=[
                        dict(name='foo', total=1234),
                        dict(type='debit', name='bar', total=56, quantity=78, 
                             amount=90, unit='unit'),
                    ],
                ),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        invoice = customer.invoice(
            amount='55.66',
            title='I want you bankrupt invoice',
            payment_uri='MOCK_PAYMENT_URI',
            items=[
                dict(name='foo', total=1234),
                dict(type='debit', name='bar', total=56, quantity=78, 
                     amount=90, unit='unit'),
            ],
            adjustments=[
                dict(total=-100, reason='A Lannister always pays his debts!'),
                dict(total=20, reason='you own me'),
            ],
        )
        self.assertEqual(invoice.guid, 'MOCK_INVOICE_GUID')

        # NOTICE: as the flexmock is not checking the data parameter, so 
        # we need to do it here
        _, data, _ = post_calls[0]
        self.assertEqual(data, dict(
            customer_guid='MOCK_CUSTOMER_GUID',
            payment_uri='MOCK_PAYMENT_URI',
            title='I want you bankrupt invoice',
            amount='55.66',
            # item1
            item_name0='foo',
            item_total0='1234',
            # item2
            item_type1='debit',
            item_name1='bar',
            item_total1='56',
            item_quantity1='78',
            item_amount1='90',
            item_unit1='unit',
            # adjustment1
            adjustment_total0='-100',
            adjustment_reason0='A Lannister always pays his debts!',
            # adjustment2
            adjustment_total1='20',
            adjustment_reason1='you own me',
        ))

    def test_invoice_with_duplicate_external_id(self):
        import requests
        from billy_client.api import Customer
        from billy_client.api import DuplicateExternalIDError

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        customer = Customer(api, dict(guid='MOCK_CUSTOMER_GUID'))

        mock_invoice_data = dict(
            guid='MOCK_INVOICE_GUID',
        )
        mock_response = flexmock(
            json=lambda: mock_invoice_data,
            status_code=409,
            content='Duplicate',
        )

        post_calls = []

        def mock_post(url, data, auth):
            post_calls.append((url, data, auth))
            return mock_response

        (
            flexmock(requests)
            .should_receive('post')
            .with_args(
                'http://localhost/v1/invoices', 
                data=dict(
                    customer_guid='MOCK_CUSTOMER_GUID',
                    amount='5566',
                ),
                auth=('MOCK_API_KEY', ''),
            )
            .replace_with(mock_post)
            .once()
        )

        with self.assertRaises(DuplicateExternalIDError):
            customer.invoice(
                amount='55.66',
                payment_uri='MOCK_PAYMENT_URI',
                external_id='duplaite one',
            )

    def _test_list_records(self, method_name, resource_url, external_id=False):
        import urlparse
        import requests
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

        get_calls = []

        def mock_get(url, auth):
            get_calls.append((url, auth))
            mock_response = flexmock(
                json=lambda: result[len(get_calls) - 1],
                status_code=200,
            )
            return mock_response

        (
            flexmock(requests)
            .should_receive('get')
            .replace_with(mock_get)
            .times(4)
        )

        method = getattr(api, method_name)
        records = method()
        self.assertEqual(map(lambda r: r.guid, records), [
            'MOCK_RECORD_GUID1',
            'MOCK_RECORD_GUID2',
            'MOCK_RECORD_GUID3',
            'MOCK_RECORD_GUID4',
            'MOCK_RECORD_GUID5',
        ])

        self.assertEqual(
            map(lambda call: call[1], get_calls),
            [('MOCK_API_KEY', '')] * 4,
        )
        self.assertEqual(
            map(lambda call: call[0].split('?')[0], get_calls),
            [resource_url] * 4,
        )
        qs_list = []
        for url, _ in get_calls:
            o = urlparse.urlparse(url)
            query = urlparse.parse_qs(o.query)
            # flatten all values
            for k, v in query.iteritems():
                query[k] = int(v[0])
            qs_list.append(query)
        self.assertEqual(
            qs_list,
            [
                dict(),
                dict(offset=2, limit=2),
                dict(offset=4, limit=2),
                dict(offset=6, limit=2),
            ]
        )

        if external_id:
            method(external_id='id')
            # TODO: add some real test for external ID here

    def test_list_customers(self):
        self._test_list_records(
            method_name='list_customers',
            resource_url='http://localhost/v1/customers',
            external_id=True,
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
            external_id=True,
        )

    def test_list_transactions(self):
        self._test_list_records(
            method_name='list_transactions',
            resource_url='http://localhost/v1/transactions',
        )
