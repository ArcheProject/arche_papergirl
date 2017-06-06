# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.api import Content
from arche.api import ContextACLMixin
from arche.api import LocalRolesMixin
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IPostOffice
from arche_papergirl.security import PERM_ADD_POST_OFFICE


@implementer(IPostOffice)
class PostOffice(Content, LocalRolesMixin, ContextACLMixin):
    type_name = "PostOffice"
    type_title = _("Post Office")
    default_view = "view"
    nav_visible = False
    listing_visible = True
    search_visible = False
    show_byline = False
    add_permission = PERM_ADD_POST_OFFICE
    css_icon = "glyphicon glyphicon-inbox"

    @property
    def subscribers(self):
        return self['s']

    def get_email_lists(self):
        """ Get email lists without checking permission """
        for obj in self.values():
            if IEmailList.providedBy(obj):
                yield obj


def includeme(config):
    config.add_content_factory(PostOffice, addable_to=('Root', 'Folder'))
