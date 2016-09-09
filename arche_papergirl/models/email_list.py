# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.api import Content
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList


@implementer(IEmailList)
class EmailList(Content):
    type_name = "EmailList"
    type_title = _("EmailList")
    default_view = "view"
    nav_visible = True
    listing_visible = True
    search_visible = False
    show_byline = False
    css_icon = "glyphicon glyphicon-send"
    title = ""
    subscribe_on_profile = False


def includeme(config):
    config.add_content_factory(EmailList, addable_to = 'PostOffice')
