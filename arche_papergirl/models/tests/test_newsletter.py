# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyClass, verifyObject

from arche_papergirl.exceptions import AlreadyInQueueError
from arche_papergirl.interfaces import INewsletter


class NewsletterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models.newsletter import Newsletter
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
