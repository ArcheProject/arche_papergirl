from arche.interfaces import IBase
from arche.interfaces import IContent
from arche.interfaces import IIndexedContent
from arche.interfaces import IThumbnailedContent
from zope.interface import Attribute


class IEmailList(IContent):
    """ Email list objects. Referenced by subscribers.
    """


class IEmailListTemplate(IContent):
    """ Used when sending a newsletter.
    """
    body = Attribute("The actual template code.")


class IListSubscriber(IBase, IIndexedContent):
    """
    """
    email = Attribute("Email address of this subscriber. May never be emty and should never change.")
    token = Attribute("Token used to access subscriber information.")


class IListSubscribers(IBase, IIndexedContent):
    """ Always attached as a singleton within PostOffice objects.
        It contains all ListSubscriber objects.
    """

    def update_cache(list_subscriber):
        """ Updates cached values
            token -> name
            email -> name
        """

    def emails():
        """
        :return: Lazy iterator of all emails contained
        """

    def email_to_subs(email, default=None):
        """ Find a subscriber object, or return default.
        """


class INewsletter(IContent, IThumbnailedContent):
    """

    """
    subject = Attribute("Email subject")
    email_template = Attribute("UID of the mail template to use.")
    queue_len = Attribute("Return an integer representing length of the queue.s")

    def add_queue(subscriber_uid, list_uid):
        """ Add a subscriber to the delivery queue.
        """

    def pop_next():
        """ pop next action from queue
        """

    def set_uid_status(uid, status, list_uid, timestamp=None):
        """ Set status for a subscriber
        """

    def get_uid_status(uid, default=None):
        """ Return current status for subscriber.
        """

    def get_uid_status_all(uid, default=None):
        """ Return the whole storage containing all status updates
        """

    def get_status():
        """ Returns a dict with number of subscribers in queue, processed and errored
        """

    def recipient_uids():
        """ All uids of subscribers that have some sort of saved status
        """

    def get_sections():
        """ All Newsletter Section objects contained.
        """


class INewsletterSection(IBase):
    """ Representing a section within a newsletter. Doesn't have to be used.
    """


class IPostOffice(IContent):
    """ Container for Papergirl operations.
    """
    subscribers = Attribute("Shortcut to the IListSubscribers object that's "
                            "always stored within a PostOffice")
