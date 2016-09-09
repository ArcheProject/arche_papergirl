# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_VIEW
from arche.views.base import BaseView, BaseForm
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList
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
            #FIXME: Specific empty page maybe?
            self.flash_messages.add(_("You're not subscribing to any lists."),
                                    type='warning',
                                    auto_destruct=False,
                                    require_commit=False)

    def appstruct(self):
        return {}

    def unsubscribe_success(self, appstruct):
        self.context.remove_lists(appstruct['lists'])
        return HTTPFound(location=self.request.url)


@view_config(route_name='confirm_subscription',
             permission=NO_PERMISSION_REQUIRED,
             renderer='arche_papergirl:templates/subscription_confirmed.pt',)
class ListSubscriberConfirm(BaseView):

    def __call__(self):
        email_list = self.request.resolve_uid(self.request.matchdict['email_list'])
        if not IEmailList.providedBy(email_list):
            raise HTTPNotFound()
        list_subscriber = self.request.resolve_uid(self.request.matchdict['list_subscriber'])
        if not IListSubscriber.providedBy(list_subscriber):
            raise HTTPNotFound()
        token = self.request.matchdict['token']
        if not (token and token == list_subscriber.token):
            raise HTTPNotFound()
        list_subscriber.add_lists(email_list.uid)
        return {'email_list': email_list}


@view_config(context=IListSubscriber,
             permission=PERM_VIEW,
             renderer='arche_papergirl:templates/list_subscriber.pt',)
class ListSubscriberView(BaseView):

    def __call__(self):
        query = "uid in any(%s)" % list(self.context.list_references)
        subscribed_lists = self.catalog_query(query, resolve=True)
        return {'subscribed_lists': subscribed_lists}

#    @view_config(name='unsubscribe', renderer='arche_papergirl:templates/unsubscribe_notice.pt')
#    def unsubscribe(self):
#        if self.token and self.token == self.context.token:
#            self.context.set_active(False)
#            return {'subscribe_url': self.request.resource_url(self.context, 'subscribe', self.context.subscribe_token)}
#        raise HTTPBadRequest(_("Token doesn't match"))


def includeme(config):
    config.add_route('confirm_subscription', '/cf/{email_list}/{list_subscriber}/{token}')
    config.scan(__name__)
