# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def default_mail_tpl(request):
    from pyramid.renderers import render
    values = {'request': request}
    return render('arche_papergirl:templates/default_mail_template.txt', values, request=request)


def fixture(config):
    from arche.testing import barebone_fixture
    from arche_papergirl.models.email_list import EmailList
    from arche_papergirl.models.post_office import PostOffice
    from arche_papergirl.models.email_list_template import EmailListTemplate
    from arche_papergirl.models.list_subscriber import ListSubscriber
    from arche_papergirl.models.list_subscribers import ListSubscribers
    from arche_papergirl.models.newsletter import Newsletter
    from arche_papergirl.models.newsletter import NewsletterSection
    root = barebone_fixture(config)
    root['postoffice'] = po = PostOffice()
    if 's' not in po:
        po['s'] = ListSubscribers()
    po['list'] = EmailList()
    po['s']['subs'] = ListSubscriber(
        email="jane_doe@betahaus.net",
        token='token',
    )
    po['newsletter'] = nl = Newsletter(title = "Hello world", description = "How are you?")
    nl['s1'] = NewsletterSection(
        title = "Ketchup",
        body = "Is it <b>really</b> made of tomatoes?"
    )
    nl['s2'] = NewsletterSection(
        title = "åäö!?",
        body = "Med svenska tecken: åäö"
    )
    po['tpl'] = EmailListTemplate()
    return root
