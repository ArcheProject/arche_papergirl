# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import string
from random import choice

from BTrees.OOBTree import OOSet
from arche.api import Base
from pyramid.traversal import find_interface
from six import string_types
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import IListSubscribers


def _create_token():
    return ''.join([choice(string.letters + string.digits) for x in range(15)])


@implementer(IListSubscriber)
class ListSubscriber(Base):
    type_name = "ListSubscriber"
    type_title = _("ListSubscriber")
    listing_visible = False
    search_visible = False
#    naming_attr = 'uid'
    email = ""
    token = ""
    modified = None

    def __init__(self, email = None, token = _create_token(), **kw):
        assert email
        self._list_references = OOSet()
        super(ListSubscriber, self).__init__(email = email, token = token, **kw)

    def get_unsubscribe_url(self, request):
        return request.resource_url(self, 'unsubscribe', self.token)

    def get_subscribe_url(self, request, email_list):
        if isinstance(email_list, string_types):
            email_list_uid = email_list
        else:
            assert IEmailList.providedBy(email_list)
            email_list_uid = email_list.uid
        return request.route_url('confirm_subscription',
                                 email_list=email_list_uid,
                                 list_subscriber=self.uid, token=self.token)

    def reset_token(self, token = _create_token()):
        self.token = token
        subscribers = find_interface(self, IListSubscribers)
        subscribers.update_cache(self)

    @property
    def list_references(self):
        return self._list_references
    @list_references.setter
    def list_references(self, value):
        self._list_references.clear()
        self._list_references.update(value)

    def add_lists(self, uids, event = True):
        if isinstance(uids, string_types):
            uids = (uids,)
        list_references = set(self.list_references)
        for uid in uids:
            if uid not in self.list_references:
                list_references.add(uid)
        if list_references != set(self.list_references):
            self.update(event=event, list_references=list_references)

    def remove_lists(self, uids, event = True):
        if isinstance(uids, string_types):
            uids = (uids,)
        list_references = set(self.list_references)
        for uid in uids:
            if uid in self.list_references:
                list_references.remove(uid)
        if list_references != set(self.list_references):
            self.update(event=event, list_references=list_references)


def includeme(config):
    config.add_content_factory(ListSubscriber)
