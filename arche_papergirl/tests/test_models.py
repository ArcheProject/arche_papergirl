# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from unittest import TestCase

from arche_papergirl.exceptions import AlreadyInQueueError
from pyramid import testing
from zope.interface.verify import verifyClass, verifyObject

from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import IListSubscribers
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.testing import fixture


class NewsletterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models import Newsletter
        return Newsletter

    def test_verify_class(self):
        self.failUnless(verifyClass(INewsletter, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(INewsletter, self._cut()))

    def test_add_queue(self):
        obj = self._cut()
        obj.add_queue('subscriber_uid', 'list_uid', 'tpl_uid')
        self.assertEqual(obj._queue[1], ('subscriber_uid', 'list_uid', 'tpl_uid'))
        self.assertEqual(obj._uid_to_status['subscriber_uid'], 1)
        self.assertRaises(AlreadyInQueueError, obj.add_queue, 'subscriber_uid', 'list_uid', 'tpl_uid')

    def test_queue_len(self):
        obj = self._cut()
        self.assertEqual(obj.queue_len, 0)
        obj.add_queue('subscriber_uid', 'list_uid', 'tpl_uid')
        self.assertEqual(obj.queue_len, 1)

    def test_pop_next(self):
        obj = self._cut()
        obj.add_queue('subscriber_uid1', 'list_uid', 'tpl_uid')
        obj.add_queue('subscriber_uid2', 'list_uid', 'tpl_uid')
        obj.add_queue('subscriber_uid3', 'list_uid', 'tpl_uid')
        self.assertEqual(obj.pop_next(), ('subscriber_uid1', 'list_uid', 'tpl_uid'))
        self.assertEqual(obj.get_uid_status('subscriber_uid1'), 0)

    def test_pop_next_empty(self):
        obj = self._cut()
        self.assertEqual(obj.pop_next(), (None, None, None))


class EmailListTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models import EmailList
        return EmailList

    def test_verify_class(self):
        self.failUnless(verifyClass(IEmailList, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IEmailList, self._cut()))


class ListSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models import ListSubscriber
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


class ListSubscribersTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models import ListSubscribers
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
        self.config.include('arche_papergirl.models')
        root = fixture(self.config)
        obj = root['postoffice']['s']
        self.assertEqual(set(obj.emails()), set(['jane_doe@betahaus.net']))
