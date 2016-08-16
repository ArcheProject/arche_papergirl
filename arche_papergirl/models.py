import string
from random import choice

from arche.api import Content
from arche.api import Base
from arche.utils import utcnow
from chameleon.zpt.template import PageTemplate
from zope.interface import implementer
from BTrees.OOBTree import OOBTree

from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl import _


def _create_token():
    return ''.join([choice(string.letters + string.digits) for x in range(10)])


@implementer(INewsletter)
class Newsletter(Content):
    type_name = "Newsletter"
    type_title = _("Newsletter")
    add_permission = "Add %s" % type_name
    css_icon = "glyphicon glyphicon-envelope"

    def __init__(self, **kw):
        self.pending = OOBTree()
        self.completed = OOBTree()
        super(Newsletter, self).__init__(**kw)

    def add_to_list(self, email_list):
        if email_list.uid not in self.pending:
            self.pending[email_list.uid] = OOBTree()
        for obj in email_list.values():
            if IListSubscriber.providedBy(obj) and obj.active == True:
                if obj.uid not in self.pending[email_list.uid]:
                    self.pending[email_list.uid][obj.uid] = utcnow()

    def process_next(self, request, list_uid):
        #FIXME: Should subscribers who've marked themselves as inactive be silently removed here?
        if list_uid in self.pending:
            for subscriber_uid in self.pending[list_uid].keys():
                del self.pending[list_uid][subscriber_uid]
                if list_uid not in self.completed:
                    self.completed[list_uid] = OOBTree()
                self.completed[list_uid][subscriber_uid] = utcnow()
                #FIXME: This may cause errors if lookup returns none
                return request.resolve_uid(subscriber_uid)


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
    title = ""
    mail_template = ""

    def create_subscriber(self, email, subscribe_token=_create_token(), unsubscribe_token=_create_token()):
        if email in self.get_emails():
            raise ValueError("%r already exists" % email)
        obj = ListSubscriber(email=email, subscribe_token=subscribe_token, unsubscribe_token=unsubscribe_token)
        self[obj.uid] = obj
        return obj

    def find_subscriber(self, email, default = None):
        assert email
        for obj in self.values():
            if IListSubscriber.providedBy(obj) and email == obj.email:
                return obj
        return default

    def get_emails(self):
        """
        :return: generator with email addresses that subscribe.
        """
        for obj in self.values():
            if IListSubscriber.providedBy(obj) and obj.active == True:
                yield obj.email


@implementer(IListSubscriber)
class ListSubscriber(Base):
    type_name = "ListSubscriber"
    type_title = _("ListSubscriber")
    listing_visible = True
    search_visible = False
    naming_attr = 'uid'
    email = ""
    active = False
    subscribe_token = ""
    unsubscribe_token = ""

    def __init__(self, **kw):
        self.completed = OOBTree()
        super(ListSubscriber, self).__init__(**kw)

    def set_active(self, status):
        #FIXME: Inject logging here
        assert isinstance(status, bool)
        self.active = status

    def get_unsubscribe_url(self, request):
        return request.resource_url(self, 'unsubscribe', self.unsubscribe_token)

    def get_subscribe_url(self, request):
        return request.resource_url(self, 'subscribe', self.subscribe_token)


def render_newsletter(request, newsletter, subscriber, email_list, **kwargs):
    assert INewsletter.providedBy(newsletter)
    assert IListSubscriber.providedBy(subscriber)
    assert IEmailList.providedBy(email_list)
    page_tpl = PageTemplate(email_list.mail_template)
    tpl_values = dict(
        newsletter = newsletter,
        subscriber = subscriber,
        email_list = email_list,
        request = request,
        **kwargs
    )
    #FIXME: Encoding, translation?
    return page_tpl.render(**tpl_values)

def includeme(config):
    config.add_content_factory(Newsletter, addable_to = 'Root')
    config.add_content_factory(NewsletterSection, addable_to = 'Newsletter')
    config.add_content_factory(EmailList, addable_to = ('Root', 'Folder'))
    config.add_content_factory(ListSubscriber, addable_to = 'EmailList')
