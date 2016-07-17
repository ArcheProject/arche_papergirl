from arche.interfaces import IThumbnailedContent, IBase
from arche.interfaces import IContent


class INewsletter(IContent, IThumbnailedContent):
    pass

class INewsletterSection(IBase):
    pass
