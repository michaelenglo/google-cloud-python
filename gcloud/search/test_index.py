# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest2


class TestIndex(unittest2.TestCase):
    PROJECT = 'project'
    INDEX_ID = 'index-id'

    def _getTargetClass(self):
        from gcloud.search.index import Index
        return Index

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _setUpConstants(self):
        import datetime
        from gcloud._helpers import UTC

        self.WHEN_TS = 1437767599.006
        self.WHEN = datetime.datetime.utcfromtimestamp(self.WHEN_TS).replace(
            tzinfo=UTC)
        self.ZONE_ID = 12345

    def _makeResource(self):
        self._setUpConstants()
        return {
            'projectId': self.PROJECT,
            'indexId': self.INDEX_ID,
            'indexedField': {
                'textFields': ['text-1', 'text-2'],
                'htmlFields': ['html-1', 'html-2'],
                'atomFields': ['atom-1', 'atom-2'],
                'dateFields': ['date-1', 'date-2'],
                'numberFields': ['number-1', 'number-2'],
                'geoFields': ['geo-1', 'geo-2'],
            }
        }

    def _makeDocumentResource(self, doc_id, rank, title):
        return {
            'docId': doc_id,
            'rank': rank,
            'fields': {
                'title': {
                    'values': [{
                        'stringValue': title,
                        'stringFormat': 'text',
                        'lang': 'en'}]
                }
            }
        }

    def _verifyResourceProperties(self, index, resource):

        self.assertEqual(index.name, resource.get('indexId'))
        field_info = resource.get('indexedField', {})
        self.assertEqual(index.text_fields, field_info.get('textFields'))
        self.assertEqual(index.html_fields, field_info.get('htmlFields'))
        self.assertEqual(index.atom_fields, field_info.get('atomFields'))
        self.assertEqual(index.date_fields, field_info.get('dateFields'))
        self.assertEqual(index.number_fields, field_info.get('numberFields'))
        self.assertEqual(index.geo_fields, field_info.get('geoFields'))

    def _verifyDocumentResource(self, documents, resource):
        from gcloud.search.document import Document
        from gcloud.search.document import StringValue
        self.assertEqual(len(documents), len(resource['documents']))
        for found, expected in zip(documents, resource['documents']):
            self.assertTrue(isinstance(found, Document))
            self.assertEqual(found.name, expected['docId'])
            self.assertEqual(found.rank, expected['rank'])
            self.assertEqual(sorted(found.fields), sorted(expected['fields']))
            for field, f_field in found.fields.items():
                e_field = expected['fields'][field]
                for f_value, e_value in zip(f_field.values, e_field['values']):
                    self.assertTrue(isinstance(f_value, StringValue))
                    self.assertEqual(f_value.string_value,
                                     e_value['stringValue'])
                    self.assertEqual(f_value.string_format,
                                     e_value['stringFormat'])
                    self.assertEqual(f_value.language,
                                     e_value['lang'])

    def test_ctor(self):
        client = _Client(self.PROJECT)
        index = self._makeOne(self.INDEX_ID, client)
        self.assertEqual(index.name, self.INDEX_ID)
        self.assertTrue(index._client is client)
        self.assertEqual(index.project, client.project)
        self.assertEqual(
            index.path,
            '/projects/%s/indexes/%s' % (self.PROJECT, self.INDEX_ID))
        self.assertEqual(index.text_fields, None)
        self.assertEqual(index.html_fields, None)
        self.assertEqual(index.atom_fields, None)
        self.assertEqual(index.date_fields, None)
        self.assertEqual(index.number_fields, None)
        self.assertEqual(index.geo_fields, None)

    def test_from_api_repr_missing_identity(self):
        self._setUpConstants()
        client = _Client(self.PROJECT)
        RESOURCE = {}
        klass = self._getTargetClass()
        with self.assertRaises(KeyError):
            klass.from_api_repr(RESOURCE, client=client)

    def test_from_api_repr_bare(self):
        self._setUpConstants()
        client = _Client(self.PROJECT)
        RESOURCE = {
            'indexId': self.INDEX_ID,
        }
        klass = self._getTargetClass()
        index = klass.from_api_repr(RESOURCE, client=client)
        self.assertTrue(index._client is client)
        self._verifyResourceProperties(index, RESOURCE)

    def test_from_api_repr_w_properties(self):
        self._setUpConstants()
        client = _Client(self.PROJECT)
        RESOURCE = self._makeResource()
        klass = self._getTargetClass()
        index = klass.from_api_repr(RESOURCE, client=client)
        self.assertTrue(index._client is client)
        self._verifyResourceProperties(index, RESOURCE)

    def test_list_documents_defaults(self):
        DOCID_1 = 'docid-one'
        RANK_1 = 2345
        TITLE_1 = 'Title One'
        DOCID_2 = 'docid-two'
        RANK_2 = 1234
        TITLE_2 = 'Title Two'
        PATH = 'projects/%s/indexes/%s/documents' % (
            self.PROJECT, self.INDEX_ID)
        TOKEN = 'TOKEN'
        DOC_1 = self._makeDocumentResource(DOCID_1, RANK_1, TITLE_1)
        DOC_2 = self._makeDocumentResource(DOCID_2, RANK_2, TITLE_2)
        DATA = {
            'nextPageToken': TOKEN,
            'documents': [DOC_1, DOC_2],
        }
        client = _Client(self.PROJECT)
        conn = client.connection = _Connection(DATA)
        index = self._makeOne(self.INDEX_ID, client)

        documents, token = index.list_documents()

        self._verifyDocumentResource(documents, DATA)
        self.assertEqual(token, TOKEN)

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self.assertEqual(req['query_params'], {})

    def test_list_documents_explicit(self):
        DOCID_1 = 'docid-one'
        RANK_1 = 2345
        TITLE_1 = 'Title One'
        DOCID_2 = 'docid-two'
        RANK_2 = 1234
        TITLE_2 = 'Title Two'
        PATH = 'projects/%s/indexes/%s/documents' % (
            self.PROJECT, self.INDEX_ID)
        TOKEN = 'TOKEN'
        DOC_1 = self._makeDocumentResource(DOCID_1, RANK_1, TITLE_1)
        DOC_2 = self._makeDocumentResource(DOCID_2, RANK_2, TITLE_2)
        DATA = {'documents': [DOC_1, DOC_2]}
        client = _Client(self.PROJECT)
        conn = client.connection = _Connection(DATA)
        index = self._makeOne(self.INDEX_ID, client)

        documents, token = index.list_documents(
            max_results=3, page_token=TOKEN, view='FULL')

        self._verifyDocumentResource(documents, DATA)
        self.assertEqual(token, None)

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self.assertEqual(req['query_params'],
                         {'pageSize': 3,
                          'pageToken': TOKEN,
                          'view': 'FULL'})


class _Client(object):

    def __init__(self, project='project', connection=None):
        self.project = project
        self.connection = connection


class _Connection(object):

    def __init__(self, *responses):
        self._responses = responses
        self._requested = []

    def api_request(self, **kw):
        from gcloud.exceptions import NotFound
        self._requested.append(kw)

        try:
            response, self._responses = self._responses[0], self._responses[1:]
        except:  # pragma: NO COVER
            raise NotFound('miss')
        else:
            return response
