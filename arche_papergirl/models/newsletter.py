# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from BTrees.LOBTree import LOBTree
from BTrees.OOBTree import OOBTree
from arche.api import Base
from arche.api import Content
from arche.utils import utcnow
from arche_papergirl.security import PERM_ADD_NEWSLETTER
from six import string_types
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
    subject = ""
    email_template = ""
    add_permission = PERM_ADD_NEWSLETTER


    def __init__(self, **kw):
        super(Newsletter, self).__init__(**kw)
        self._queue = LOBTree()
        self._uid_to_status = OOBTree()

    def add_queue(self, subscriber_uid, list_uid):
        if subscriber_uid in self._uid_to_status:
            raise AlreadyInQueueError("%s already in queue" % subscriber_uid)
        try:
            key = self._queue.maxKey()+1
        except ValueError:
            key = 1
        self._queue[key] = (subscriber_uid, list_uid)
        self.set_uid_status(subscriber_uid, key, list_uid)

    @property
    def queue_len(self):
        return len(self._queue)

    def pop_next(self):
        try:
            key = self._queue.minKey()
        except ValueError:
            return None, None, None
        subscriber_uid, list_uid = self._queue.pop(key)
        self.set_uid_status(subscriber_uid, 0, list_uid)
        return subscriber_uid, list_uid

    def set_uid_status(self, uid, status, list_uid, timestamp = utcnow()):
        """
        :param uid: subscribers uid
        :param status: an integer that indicates status.
            Either 0 for delivered, a positive for in queue or a negative referencing an error.
        :param list_uid: UID of email list that was the reason this letter should be sent.
        :param timestamp: Localized datetime object with timestamp
        :return:
        """
        assert isinstance(uid, string_types)
        assert isinstance(status, int)
        assert isinstance(uid, string_types)
        if uid not in self._uid_to_status:
            self._uid_to_status[uid] = LOBTree()
        if not len(self._uid_to_status[uid]):
            entry_key = 1
        else:
            entry_key = self._uid_to_status[uid].maxKey() + 1
        self._uid_to_status[uid][entry_key] = (status, list_uid, timestamp)

    def get_uid_status(self, uid, default = None):
        try:
            storage = self._uid_to_status[uid]
        except KeyError:
            return default
        try:
            latest = storage.maxKey()
        except ValueError:
            return default
        return storage[latest]

    def get_uid_status_all(self, uid, default = None):
        try:
            return self._uid_to_status[uid]
        except KeyError:
            return default

    def get_status(self):
        results = {'queue': 0, 'delivered': 0, 'error': 0}
        for uid in self.recipient_uids():
            i = self.get_uid_status(uid)[0]
            if i > 0:
                results['queue'] += 1
            if i == 0:
                results['delivered'] += 1
            if i < 0:
                results['error'] += 1
        return results

    def recipient_uids(self):
        return self._uid_to_status.keys()

    def get_sections(self):
        for obj in self.values():
            if INewsletterSection.providedBy(obj):
                yield obj


@implementer(INewsletterSection)
class NewsletterSection(Base):
    type_name = "NewsletterSection"
    type_title = _("NewsletterSection")
    naming_attr = 'uid'
    title = ""
    body = ""


def includeme(config):
    config.add_content_factory(Newsletter, addable_to = 'PostOffice', addable_in = 'File')
    config.add_content_factory(NewsletterSection, addable_to = 'Newsletter')
