# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_VIEW
from arche.views.base import BaseView, BaseForm
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from arche_papergirl import _
from arche_papergirl.interfaces import IListSubscriber


@view_config(context=IListSubscriber,
             name='unsubscribe',
             permission=NO_PERMISSION_REQUIRED,
             renderer='arche:templates/form.pt')
class ListSubscriberUnsubscribe(BaseForm):
    type_name = 'ListSubscriber'
    schema_name = 'manage_unsubscribe'

    buttons = (deform.Button('unsubscribe', title = _("Unsubscribe"), css_class='btn-danger'),)

    def __init__(self, context, request):
        super(ListSubscriberUnsubscribe, self).__init__(context, request)
        try:
            token = request.subpath[0]
        except IndexError:
            raise HTTPNotFound()
        if not (token and token == context.token):
            raise HTTPNotFound()
        if not context.list_references:
            raise HTTPFound(location=self.request.resource_url(self.request.root, 'not_subscribing'))

    def appstruct(self):
        return {}

    def unsubscribe_success(self, appstruct):
        self.context.remove_lists(appstruct['lists'])
        return HTTPFound(location=self.request.url)


@view_config(context=IListSubscriber,
             permission=PERM_VIEW,
             renderer='arche_papergirl:templates/list_subscriber.pt',)
class ListSubscriberView(BaseView):

    def __call__(self):
        query = "uid in any(%s)" % list(self.context.list_references)
        subscribed_lists = self.catalog_query(query, resolve=True)
        return {'subscribed_lists': subscribed_lists}


def includeme(config):
    config.scan(__name__)
