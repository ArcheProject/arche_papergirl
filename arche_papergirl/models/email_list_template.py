# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.api import Content
from arche_papergirl.security import PERM_ADD_TEMPLATE
from persistent.list import PersistentList
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailListTemplate


@implementer(IEmailListTemplate)
class EmailListTemplate(Content):
    type_name = "EmailListTemplate"
    type_title = _("Email list template")
    default_view = "view"
    nav_visible = False
    listing_visible = True
    search_visible = False
    show_byline = False
    css_icon = "glyphicon glyphicon-duplicate"
    add_permission = PERM_ADD_TEMPLATE
    body = ""
    use_premailer = True
    _include_css = ()

    @property
    def include_css(self):
        return list(self._include_css)
    @include_css.setter
    def include_css(self, value):
        self._include_css = PersistentList(value)


def includeme(config):
    config.add_content_factory(EmailListTemplate, addable_to = 'PostOffice')
