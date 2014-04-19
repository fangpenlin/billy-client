from __future__ import unicode_literals
import os
import unittest

import balanced

from billy_client import BillyAPI
from billy_client import Plan


@unittest.skipUnless(
    os.environ.get('BILLY_CLIENT_TEST_AGAINST_SERVER'),
    'Skip testing against server unless BILLY_CLIENT_TEST_AGAINST_SERVER is set',
)
class TestAgainstServer(unittest.TestCase):

    def setUp(self):
        self.target_url = os.environ.get(
            'BILLY_TEST_URL',
            'http://127.0.0.1:6543')
        self.processor_key = os.environ.get(
            'BILLY_TEST_PROCESSOR_KEY',
            'ef13dce2093b11e388de026ba7d31e6f')
        self.marketplace_uri = os.environ.get(
            'BILLY_TEST_MARKETPLACE_URI',
            '/v1/marketplaces/TEST-MP6lD3dBpta7OAXJsN766qA')
        balanced.configure(self.processor_key)

    def make_one(self, api_key, endpoint=None):
        if endpoint is None:
            endpoint = self.target_url
        return BillyAPI(api_key, endpoint=endpoint)

    def test_basic_scenario(self):
        api = self.make_one(None)

        marketplace = balanced.Marketplace.find(self.marketplace_uri)
        # create a card to charge
        card = marketplace.create_card(
            name='BILLY_INTERGRATION_TESTER',
            card_number='5105105105105100',
            expiration_month='12',
            expiration_year='2020',
            security_code='123',
        )

        company = api.create_company(processor_key=self.processor_key)
        api_key = company.api_key
        api = self.make_one(api_key)

        customer = company.create_customer()
        plan = company.create_plan(
            plan_type=Plan.TYPE_DEBIT,
            frequency=Plan.FREQ_DAILY,
            amount=7788,
        )
        subscription = plan.subscribe(
            customer_guid=customer.guid,
            funding_instrument_uri=card.uri,
            appears_on_statement_as='hello baby',
        )
        self.assertEqual(subscription.customer_guid, customer.guid)
        self.assertEqual(subscription.plan_guid, plan.guid)
        self.assertEqual(subscription.funding_instrument_uri, card.uri)
        self.assertEqual(subscription.appears_on_statement_as, 'hello baby')

        # check invoice
        invoices = list(subscription.list_invoices())
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.subscription_guid, subscription.guid)

        # check charge transaction
        transactions = list(subscription.list_transactions())
        self.assertEqual(len(transactions), 1)
        transaction = transactions[0]
        self.assertEqual(transaction.invoice_guid, invoice.guid)

        # check corresponding debit transaction in Balanced
        debit = balanced.Debit.find(transaction.processor_uri)
        self.assertEqual(debit.meta['billy.transaction_guid'], transaction.guid)
        self.assertEqual(debit.amount, 7788)
        self.assertEqual(debit.status, 'succeeded')
        self.assertEqual(debit.appears_on_statement_as, 'hello baby')

        # cancel the subscription
        subscription = subscription.cancel()
        self.assertEqual(subscription.canceled, True)

        # refund the invoice
        invoice = invoice.refund(amount=1234)

        # check the refund transaction
        transactions = list(subscription.list_transactions())
        self.assertEqual(len(transactions), 2)
        transaction = transactions[0]
        self.assertEqual(transaction.invoice_guid, invoice.guid)
        self.assertEqual(transaction.submit_status, 'done')
        self.assertEqual(transaction.transaction_type, 'refund')

        # check the refund transaction in Balanced
        refund = balanced.Refund.find(transaction.processor_uri)
        self.assertEqual(refund.meta['billy.transaction_guid'],
                         transaction.guid)
        self.assertEqual(refund.amount, 1234)
        self.assertEqual(refund.status, 'succeeded')
