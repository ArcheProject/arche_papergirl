# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import string
from random import choice

from BTrees.OOBTree import OOBTree
from BTrees.LOBTree import LOBTree
from BTrees.OLBTree import OLBTree
from BTrees.OOBTree import OOSet
from arche.api import Base
from arche.api import Content
from arche.interfaces import IObjectAddedEvent
from arche.interfaces import IObjectUpdatedEvent
from arche.interfaces import IUser
from arche.utils import utcnow
from arche_papergirl.exceptions import AlreadyInQueueError
from pyramid.threadlocal import get_current_request
from six import string_types
from zope.interface import implementer
from repoze.folder import Folder
from pyramid.traversal import find_interface

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IPostOffice
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import IListSubscribers
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection


def _create_token():
    return ''.join([choice(string.letters + string.digits) for x in range(15)])


@implementer(INewsletter)
class Newsletter(Content):
    type_name = "Newsletter"
    type_title = _("Newsletter")
    add_permission = "Add %s" % type_name
    css_icon = "glyphicon glyphicon-envelope"

    def __init__(self, **kw):
        super(Newsletter, self).__init__(**kw)
        self._queue = LOBTree()
        self._uid_to_status = OLBTree()

    def add_queue(self, subscriber_uid, list_uid, tpl_uid):
        if subscriber_uid in self._uid_to_status:
            raise AlreadyInQueueError("%s already in queue" % subscriber_uid)
        try:
            key = self._queue.maxKey()+1
        except ValueError:
            key = 1
        self._queue[key] = (subscriber_uid, list_uid, tpl_uid)
        self.set_uid_status(subscriber_uid, key)

    @property
    def queue_len(self):
        return len(self._queue)

    def pop_next(self):
        try:
            key = self._queue.minKey()
        except ValueError:
            return None, None, None
        subscriber_uid, list_uid, tpl_uid = self._queue.pop(key)
        self.set_uid_status(subscriber_uid, 0)
        return subscriber_uid, list_uid, tpl_uid

    def set_uid_status(self, uid, status):
        self._uid_to_status[uid] = status

    def get_uid_status(self, uid, default = None):
        return self._uid_to_status.get(uid, default)


@implementer(INewsletterSection)
class NewsletterSection(Base):
    type_name = "NewsletterSection"
    type_title = _("NewsletterSection")
    naming_attr = 'uid'
    title = ""
    body = ""


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


@implementer(IPostOffice)
class PostOffice(Content):
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


@implementer(IListSubscriber)
class ListSubscriber(Base):
    type_name = "ListSubscriber"
    type_title = _("ListSubscriber")
    listing_visible = False
    search_visible = False
#    naming_attr = 'uid'
    email = ""
    token = ""

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
        #return request.resource_url(self, 'subscribe', self.token, email_list_uid)

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
        self._adj_list(uids, 'add', event=event)

    def remove_lists(self, uids, event = True):
        self._adj_list(uids, 'remove', event=event)

    def _adj_list(self, uids, operator, event):
        if isinstance(uids, string_types):
            uids = (uids,)
            list_references = set(self.list_references)
        for uid in uids:
            if uid in self.list_references:
                getattr(list_references, operator)(uid)
        if list_references != set(self.list_references):
            self.update(event=event, list_references=list_references)


def get_email_lists(request=None):
    if request is None:
        request = get_current_request()
    query = "type_name == 'EmailList'"
    docids = request.root.catalog.query(query)[1]
    return request.resolve_docids(docids)


def get_email_templates(request=None):
    if request is None:
        request = get_current_request()
    query = "type_name == 'EmailListTemplate'"
    docids = request.root.catalog.query(query)[1]
    return request.resolve_docids(docids)


def _get_valid_lists():
    for obj in get_email_lists():
        if obj.subscribe_on_profile:
            yield obj


# def subscribe_on_profile(config):
#     from arche.api import User
#
#     #Subscriber for adjusting lists
#     config.add_subscriber(_update_lists_with_pending_profile_changes, [IUser, IObjectUpdatedEvent])
#     config.add_subscriber(_update_lists_with_pending_profile_changes, [IUser, IObjectAddedEvent])
#
#     #Add a proxy attribute to User that delegates settings to email lists
#     def _get_email_subscriptions(self):
#         #FIXME: Make sure sure user email is validated before adding the widget?
#         request = get_current_request()
#         query = "type_name == 'ListSubscriber' and email == '%s'" % self.email
#         docids = request.root.catalog.query(query)[1]
#         results = set()
#         for obj in request.resolve_docids(docids):
#             results.update(obj.list_references)
#         return results
#
#         # found_lists = set()
#         # if not self.email:
#         #     return found_lists
#         # for obj in _get_valid_lists():
#         #     subscr = obj.find_subscriber(self.email)
#         #     if subscr != None and subscr.active == True:
#         #         found_lists.add(obj.uid)
#         # return found_lists
#     def _set_email_subscriptions(self, value):
#         print "setting pending changes: ", value
#         self._pending_list_changes = frozenset(value)
#     User._email_list_subscriptions = property(_get_email_subscriptions, _set_email_subscriptions)
#
#
# def _update_lists_with_pending_profile_changes(user, event):
#     return
#
#     #FIXME
#     if not user.email or not hasattr(user, '_pending_list_changes'):
#         return
#     if not getattr(event, 'changed', ()) or '_email_list_subscriptions' in event.changed:
#         pending_lists = user._pending_list_changes
#         for obj in _get_valid_lists():
#             subscr = obj.find_subscriber(user.email)
#             if subscr:
#                 #Adjust existing
#                 if subscr.active == False and obj.uid in pending_lists:
#                     subscr.set_active(True)
#                 if subscr.active == True and obj.uid not in pending_lists:
#                     subscr.set_active(False)
#             elif obj.uid in pending_lists and subscr is None:
#                 #Create subscriber
#                 subscr = obj.create_subscriber(user.email)
#                 subscr.set_active(True)
#         delattr(user, '_pending_list_changes')
#
#
# def _add_list_subscribers(context, event):
#     request = get_current_request()
#     context['s'] = request.content_factories['ListSubscribers']()
#
#
def _cache_subscribers_info(context, event):
    list_subscribers = find_interface(context, IListSubscribers)
    if list_subscribers:
        list_subscribers.update_cache(context)


def includeme(config):
    config.add_content_factory(PostOffice, addable_to = ('Root', 'Folder'))
    config.add_content_factory(Newsletter, addable_to = 'PostOffice')
    config.add_content_factory(NewsletterSection, addable_to = 'Newsletter')
    config.add_content_factory(EmailList, addable_to = 'PostOffice')
    config.add_content_factory(ListSubscriber)
    config.add_content_factory(EmailListTemplate, addable_to = 'PostOffice')
    config.add_content_factory(ListSubscribers)
    #config.add_subscriber(_add_list_subscribers, [IPostOffice, IObjectAddedEvent])
    config.add_subscriber(_cache_subscribers_info, [IListSubscriber, IObjectAddedEvent])
    config.add_subscriber(_cache_subscribers_info, [IListSubscriber, IObjectUpdatedEvent])
