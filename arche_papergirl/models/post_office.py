# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.api import Content
from arche.api import LocalRolesMixin, ContextACLMixin
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IPostOffice


@implementer(IPostOffice)
class PostOffice(Content, LocalRolesMixin, ContextACLMixin):
    type_name = "PostOffice"
    type_title = _("Post Office")
    default_view = "view"
    nav_visible = False
    listing_visible = True
    search_visible = False
    show_byline = False
    css_icon = "glyphicon glyphicon-inbox"

    @property
    def subscribers(self):
        return self['s']


def includeme(config):
    config.add_content_factory(PostOffice, addable_to=('Root', 'Folder'))
