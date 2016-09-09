# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.api import Content
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailListTemplate


@implementer(IEmailListTemplate)
class EmailListTemplate(Content):
    type_name = "EmailListTemplate"
    type_title = _("EmailList Template")
    default_view = "view"
    nav_visible = False
    listing_visible = True
    search_visible = False
    show_byline = False
    css_icon = "glyphicon glyphicon-duplicate"
    body = ""


def includeme(config):
    config.add_content_factory(EmailListTemplate, addable_to = 'PostOffice')
