# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyClass, verifyObject

from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.testing import fixture


class ListSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models.list_subscriber import ListSubscriber
        return ListSubscriber

    def test_verify_class(self):
        self.failUnless(verifyClass(IListSubscriber, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IListSubscriber, self._cut("hello@world.com")))

    def test_get_unsubscribe_url(self):
        root = fixture(self.config)
        obj = root['postoffice']['s']['subs']
        request = testing.DummyRequest()
        self.assertEqual(obj.get_unsubscribe_url(request), "http://example.com/postoffice/s/subs/unsubscribe/token")

    def test_get_subscribe_url(self):
        self.config.include('arche_papergirl.views')
        root = fixture(self.config)
        obj = root['postoffice']['s']['subs']
        obj.uid = 'subs_uid'
        email_list = root['postoffice']['list']
        email_list.uid = 'el_uid'
        request = testing.DummyRequest()
        self.assertEqual(obj.get_subscribe_url(request, email_list), "http://example.com/cf/el_uid/subs_uid/token")
