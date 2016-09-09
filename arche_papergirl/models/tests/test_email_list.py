# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyClass, verifyObject

from arche_papergirl.interfaces import IEmailList


class EmailListTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from arche_papergirl.models.email_list import EmailList
        return EmailList

    def test_verify_class(self):
        self.failUnless(verifyClass(IEmailList, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IEmailList, self._cut()))

