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
            .once()
        )

        api = self.make_one(None, endpoint='http://localhost')
        company = api.create_company('MOCK_PROCESSOR_KEY')
        self.assertEqual(company.guid, 'CPMOCK_COMPANY')
        self.assertEqual(company.api, api)

    def test_get_company(self):
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
            .should_receive('get')
            .with_args('http://localhost/v1/companies/CPMOCK_COMPANY', 
                       auth=('MOCK_API_KEY', ''))
            .replace_with(lambda url, auth: mock_response)
            .once()
        )

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        company = api.get_company('CPMOCK_COMPANY')
        self.assertEqual(company.guid, 'CPMOCK_COMPANY')
        self.assertEqual(company.api, api)

    def test_get_company_not_found(self):
        import requests
        from billy_client import BillyNotFoundError

        mock_company_data = dict(
            guid='CPMOCK_COMPANY',
        )

        mock_response = flexmock(
            json=lambda: mock_company_data,
            status_code=404,
            content='Not found',
        )

        (
            flexmock(requests)
            .should_receive('get')
            .with_args('http://localhost/v1/companies/CPMOCK_COMPANY', 
                       auth=('MOCK_API_KEY', ''))
            .replace_with(lambda url, auth: mock_response)
            .once()
        )

        api = self.make_one('MOCK_API_KEY', endpoint='http://localhost')
        with self.assertRaises(BillyNotFoundError):
            api.get_company('CPMOCK_COMPANY')
