# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from unittest import TestCase

from arche.testing import barebone_fixture
from pyramid import testing
from pyramid.renderers import render
from zope.interface.verify import verifyClass, verifyObject

from arche_papergirl.interfaces import INewsletter, IEmailList, IListSubscriber


def _default_mail_tpl(request):
    values = {'request': request}
    return render('arche_papergirl:templates/default_mail_template.txt', values, request=request)

def _fixture(config):
    from arche_papergirl.models import EmailList
    from arche_papergirl.models import ListSubscriber
    from arche_papergirl.models import Newsletter
    from arche_papergirl.models import NewsletterSection
    root = barebone_fixture(config)
    root['list'] = EmailList()
    root['list']['subs'] = ListSubscriber(email="jane_doe@betahaus.net",
                                          subscribe_token='sub_token',
                                          unsubscribe_token='unsub_token',
                                          active=True)
    root['newsletter'] = nl = Newsletter(title = "Hello world", description = "How are you?")
    nl['s1'] = NewsletterSection(title = "Ketchup",
                                 body = "Is it <b>really</b> made of tomatoes?")
    nl['s2'] = NewsletterSection(title = "åäö!?",
                                 body = "Med svenska tecken: åäö")
    return root


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

    def test_add_to_list(self):
        root = _fixture(self.config)
        obj = root['newsletter']
        obj.add_to_list(root['list'])
        email_list = root['list']
        subscriber = root['list']['subs']
        self.assertIn(email_list.uid, obj.pending)
        self.assertIn(subscriber.uid, obj.pending[email_list.uid])
        self.assertIsInstance(obj.pending[email_list.uid][subscriber.uid], datetime)

    def test_process_next(self):
        from pyramid.request import apply_request_extensions
        self.config.include('arche.testing')
        self.config.include('arche.testing.catalog')
        root = _fixture(self.config)
        obj = root['newsletter']
        obj.add_to_list(root['list'])
        email_list = root['list']
        subscriber = root['list']['subs']
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.root = root
        processed_subscriber = obj.process_next(request, email_list.uid)
        self.assertEqual(subscriber, processed_subscriber)
        self.assertNotIn(subscriber.uid, obj.pending[email_list.uid])
        self.assertIn(subscriber.uid, obj.completed[email_list.uid])
        self.assertIsInstance(obj.completed[email_list.uid][subscriber.uid], datetime)


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

    def test_create_subscriber(self):
        obj = self._cut()
        subscriber = obj.create_subscriber("jane_doe@betahaus.net",
                                           subscribe_token='subscribe',
                                           unsubscribe_token='unsubscribe')
        self.assertTrue(IListSubscriber.providedBy(subscriber))
        self.assertEqual(subscriber.subscribe_token, 'subscribe')
        self.assertEqual(subscriber.unsubscribe_token, 'unsubscribe')
        self.assertIn(subscriber.uid, obj)

    def test_find_subscriber(self):
        obj = self._cut()
        subscriber = obj.create_subscriber("jane_doe@betahaus.net")
        self.assertEqual(subscriber, obj.find_subscriber("jane_doe@betahaus.net"))
        self.assertEqual(None, obj.find_subscriber("404@betahaus.net"))

    def test_get_emails(self):
        obj = self._cut()
        subscriber = obj.create_subscriber("jane_doe@betahaus.net")
        subscriber.active = True
        self.assertEqual(tuple(obj.get_emails()), ("jane_doe@betahaus.net",))
        subscriber.active = False
        self.assertEqual(tuple(obj.get_emails()), ())


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
        self.failUnless(verifyObject(IListSubscriber, self._cut()))

    def test_set_active(self):
        obj = self._cut()
        obj.set_active(True)
        self.assertEqual(obj.active, True)

    def test_get_unsubscribe_url(self):
        root = _fixture(self.config)
        obj = root['list']['subs']
        request = testing.DummyRequest()
        self.assertEqual(obj.get_unsubscribe_url(request), "http://example.com/list/subs/unsubscribe/unsub_token")

    def test_get_subscribe_url(self):
        root = _fixture(self.config)
        obj = root['list']['subs']
        request = testing.DummyRequest()
        self.assertEqual(obj.get_subscribe_url(request), "http://example.com/list/subs/subscribe/sub_token")


class RenderNewsletterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from arche_papergirl.models import render_newsletter
        return render_newsletter

    def test_render_dummy(self):
        root = _fixture(self.config)
        request = testing.DummyRequest()
        subscriber = root['list']['subs']
        root['list'].mail_template = "Hello ${name}"
        result = self._fut(request, root['newsletter'], subscriber, root['list'], name = 'World')
        self.assertEqual(result, "Hello World")

    def test_render_default(self):
        self.config.include('pyramid_chameleon')
        root = _fixture(self.config)
        request = testing.DummyRequest()
        email_list = root['list']
        email_list.mail_template = _default_mail_tpl(request)
        result = self._fut(request, root['newsletter'], root['list']['subs'], email_list)
        self.assertIn("åäö!?", result)
        self.assertIn("http://example.com/list/subs/unsubscribe/unsub_token", result)
