# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from BTrees.OOBTree import OOSet
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

    def test_list_references(self):
        obj = self._cut("hello@betahaus.net")
        obj.list_references.add('123')
        self.assertEqual(set(obj.list_references), set(['123']))
        obj.list_references = ['123', 'abc']
        self.assertEqual(set(obj.list_references), set(['123', 'abc']))
        self.assertIsInstance(obj.list_references, OOSet)

    def test_add_lists(self):
        obj = self._cut("hello@betahaus.net")
        obj.add_lists('1')
        obj.add_lists(['2', '3'])
        obj.add_lists('1')
        self.assertEqual(set(obj.list_references), set(['1', '2', '3']))

    def test_remove_lists(self):
        obj = self._cut("hello@betahaus.net")
        obj.list_references = ('1', '2', '3')
        obj.remove_lists('2')
        obj.remove_lists(['3', '4'])
        self.assertEqual(set(obj.list_references), set(['1']))

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
