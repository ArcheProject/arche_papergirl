# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from BTrees.LOBTree import LOBTree
from BTrees.OLBTree import OLBTree
from arche.api import Base
from arche.api import Content
from zope.interface import implementer

from arche_papergirl import _
from arche_papergirl.exceptions import AlreadyInQueueError
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection


@implementer(INewsletter)
class Newsletter(Content):
    """ Newsletter objects

        about statuses
        Any positive status for uid should be it's queue position
        0 means that it's done
        A negative number is held for indicating other things
    """
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

    def get_status(self):
        results = {'queue': 0, 'delivered': 0, 'error': 0}
        for i in self._uid_to_status.values():
            if i > 0:
                results['queue'] += 1
            if i == 0:
                results['delivered'] += 1
            if i < 0:
                results['error'] += 1
        return results


@implementer(INewsletterSection)
class NewsletterSection(Base):
    type_name = "NewsletterSection"
    type_title = _("NewsletterSection")
    naming_attr = 'uid'
    title = ""
    body = ""


def includeme(config):
    config.add_content_factory(Newsletter, addable_to = 'PostOffice')
    config.add_content_factory(NewsletterSection, addable_to = 'Newsletter')
