from __future__ import unicode_literals
import json
import unittest

from flexmock import flexmock


class TestAPI(unittest.TestCase):

    def make_one(self, *args, **kwargs):
        from billy_client.api import BillyAPI
        return BillyAPI(*args, **kwargs)

    def test_create_company(self):
        import requests

        mock_company_data = dict(
            guid='CPMOCK_COMPANY',
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
        )

        api = self.make_one(None, endpoint='http://localhost')
        company = api.create_company('MOCK_PROCESSOR_KEY')
        self.assertEqual(company.guid, 'CPMOCK_COMPANY')
