from arche.interfaces import IObjectAddedEvent
from arche.interfaces import IObjectUpdatedEvent
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface

from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import IListSubscribers
from arche_papergirl.interfaces import IPostOffice


def cache_subscribers_info(context, event):
    list_subscribers = find_interface(context, IListSubscribers)
    if list_subscribers:
        list_subscribers.update_cache(context)


def add_list_subscribers(context, event):
    request = get_current_request()
    context['s'] = request.content_factories['ListSubscribers']()


def includeme(config):
    config.add_subscriber(cache_subscribers_info, [IListSubscriber, IObjectAddedEvent])
    config.add_subscriber(cache_subscribers_info, [IListSubscriber, IObjectUpdatedEvent])
    config.add_subscriber(add_list_subscribers, [IPostOffice, IObjectAddedEvent])
