from arche.api import Content
from arche.resources import Base
from zope.interface import implementer

from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl import _


@implementer(INewsletter)
class Newsletter(Content):
    type_name = "Newsletter"
    type_title = _("Newsletter")
    add_permission = "Add %s" % type_name
    css_icon = "glyphicon glyphicon-envelope"


@implementer(INewsletterSection)
class NewsletterSection(Base):
    type_name = "NewsletterSection"
    type_title = _("NewsletterSection")
    naming_attr = 'uid'
    title = ""
    body = ""


def includeme(config):
    config.add_content_factory(Newsletter, addable_to = 'Root')
    config.add_content_factory(NewsletterSection, addable_to = 'Newsletter')
