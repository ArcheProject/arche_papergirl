# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from BTrees.OOBTree import OOBTree
from arche.api import Content
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IListSubscribers


@implementer(IListSubscribers)
class ListSubscribers(Content):
    type_name = "ListSubscribers"
    type_title = _("List subscribers")
    default_view = "view"
    nav_visible = False
    listing_visible = True
    search_visible = False
    show_byline = False
    css_icon = "glyphicon glyphicon-user"
    title = type_title

    def __init__(self, **kw):
        self._token_to_name = OOBTree()
        self._email_to_name = OOBTree()
        super(ListSubscribers, self).__init__(**kw)

    # def __getitem__(self, name):
    #     """ Custom method to override default traversal behaviour.
    #         Enables lookup via token
    #     """
    #     try:
    #         return self.data[name]
    #     except KeyError:
    #         return self.data[self._token_to_name[name]]

    def update_cache(self, list_subscriber):
        self._token_to_name[list_subscriber.token] = list_subscriber.__name__
        self._email_to_name[list_subscriber.email] = list_subscriber.__name__

    def emails(self):
        return self._email_to_name.keys()

    def email_to_subs(self, email, default=None):
        try:
            return self[self._email_to_name[email]]
        except KeyError:
            return default


def includeme(config):
    config.add_content_factory(ListSubscribers)
