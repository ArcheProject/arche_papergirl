from arche.interfaces import IBase
from arche.interfaces import IContent
from arche.interfaces import IIndexedContent
from arche.interfaces import IThumbnailedContent


class INewsletter(IContent, IThumbnailedContent):
    pass


class INewsletterSection(IBase):
    pass


class IEmailList(IContent):
    pass


class IPostOffice(IContent):
    pass


class IEmailQueue(IBase, IIndexedContent):
    pass


class IEmailListTemplate(IContent):
    pass


class IListSubscriber(IBase, IIndexedContent):
    pass


class IListSubscribers(IBase, IIndexedContent):
    pass
