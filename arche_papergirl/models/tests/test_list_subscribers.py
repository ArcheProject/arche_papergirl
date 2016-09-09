# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyClass, verifyObject
from pyramid.request import apply_request_extensions

from arche_papergirl.interfaces import IListSubscribers
from arche_papergirl.testing import fixture


class ListSubscribersTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models.list_subscribers import ListSubscribers
        return ListSubscribers

    def test_verify_class(self):
        self.failUnless(verifyClass(IListSubscribers, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IListSubscribers, self._cut()))

    def test_update_cache(self):
        root = fixture(self.config)
        po = root['postoffice']
        obj = po['s']
        subs = po['s']['subs']
        obj.update_cache(subs)
        self.assertIn('token', obj._token_to_name)
        self.assertEqual(subs.__name__, obj._token_to_name['token'])
        self.assertIn('jane_doe@betahaus.net', obj._email_to_name)
        self.assertEqual(subs.__name__, obj._email_to_name['jane_doe@betahaus.net'])
        subs.token = 'othert'
        subs.email = 'robin@betahaus.net'
        obj.update_cache(subs)
        self.assertIn('othert', obj._token_to_name)
        self.assertIn('robin@betahaus.net', obj._email_to_name)

    def test_emails(self):
        self.config.include('arche.testing')
        self.config.include('arche.testing.catalog')
        self.config.include('arche_papergirl.subscribers')
        self.config.include('arche_papergirl.models')
        request = testing.DummyRequest()
        self.config.begin(request)
        apply_request_extensions(request)
        root = fixture(self.config)
        request.root = root
        obj = root['postoffice']['s']
        self.assertEqual(set(obj.emails()), set(['jane_doe@betahaus.net']))
