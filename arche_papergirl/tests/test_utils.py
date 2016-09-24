# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

from pyramid import testing

from arche_papergirl.testing import fixture
from arche_papergirl.testing import default_mail_tpl


class RenderNewsletterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from arche_papergirl.utils import render_newsletter
        return render_newsletter

    def test_render_dummy(self):
        root = fixture(self.config)
        request = testing.DummyRequest()
        po = root['postoffice']
        subscriber = po['s']['subs']
        po['tpl'].body = "Hello ${name}"
        result = self._fut(request, po['newsletter'], subscriber, po['list'], po['tpl'], name = 'World')
        self.assertIn("Hello World", result)

    def test_render_default(self):
        self.config.include('pyramid_chameleon')
        request = testing.DummyRequest()
        root = fixture(self.config)
        po = root['postoffice']
        email_list = po['list']
        po['tpl'].body = default_mail_tpl(request)
        result = self._fut(request, po['newsletter'], po['s']['subs'], email_list, po['tpl'])
        self.assertIn("åäö!?", result)
        self.assertIn("http://example.com/postoffice/s/subs/unsubscribe/token", result)
