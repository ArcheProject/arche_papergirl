# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche import security
from arche.interfaces import IRoot
from arche.security import NO_PERMISSION_REQUIRED
from arche.views.base import BaseForm
from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import find_interface
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import IPostOffice


@view_defaults(context = IRoot, permission = security.NO_PERMISSION_REQUIRED)
class MessagesView(BaseView):

    @view_config(name='pending_confirm', renderer='arche_papergirl:templates/confirm_subscription.pt')
    def pending_confirm(self):
        return {}

    @view_config(name='not_subscribing', renderer='arche_papergirl:templates/not_subscribing.pt')
    def not_subscribing(self):
        return {}


@view_config(context = IEmailList,
             name = 'request',
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class RequestSubscriptionForm(BaseForm):
    schema_name = "subscribe"
    type_name = "EmailList"
    buttons = (deform.Button('subscribe', title=_("Subscribe")),)
    use_ajax = True
    ajax_options = """
        {success:
          function (rText, sText, xhr, form) {
            arche.load_flash_messages();
           }
        }
    """

    def __call__(self):
        if self.context.allow_subscription:
            return super(RequestSubscriptionForm, self).__call__()
        raise HTTPForbidden("Self-subscription not allowed")

    @property
    def form_options(self):
        form_options = super(RequestSubscriptionForm, self).form_options
        form_options['action'] = self.request.resource_url(self.context, 'request')
        return form_options

    def subscribe_success(self, appstruct):
        post_office = find_interface(self.context, IPostOffice)
        email = appstruct['email']
        subs = post_office.subscribers.email_to_subs(email)
        if subs is None:
            subs = self.request.content_factories['ListSubscriber'](email=email)
            post_office.subscribers[subs.uid] = subs
        url = subs.get_subscribe_url(self.request, self.context)
        html = self.render_template("arche_papergirl:templates/mail_subscribe.pt", context = self.context, url = url)
        subject = _("${title} subscription request",
                    mapping = {'title': self.context.title})
        self.request.send_email(subject,
                                [appstruct['email']],
                                html,
                                send_immediately = True)
        return HTTPFound(location=self.request.resource_url(self.request.root, 'pending_confirm'))


@view_config(route_name='confirm_subscription',
             permission=NO_PERMISSION_REQUIRED,)
class ListSubscriberConfirm(BaseView):

    def __call__(self):
        email_list = self.request.resolve_uid(self.request.matchdict['email_list'], perm=None)
        if not IEmailList.providedBy(email_list):
            raise HTTPNotFound("Email list not found")
        list_subscriber = self.request.resolve_uid(self.request.matchdict['list_subscriber'], perm=None)
        if not IListSubscriber.providedBy(list_subscriber):
            raise HTTPNotFound("List subscriber not found")
        token = self.request.matchdict['token']
        if not (token and token == list_subscriber.token):
            raise HTTPNotFound("Token doesn't match")
        list_subscriber.add_lists(email_list.uid)
        msg = _("All done, you're now subscribing to ${title}",
                mapping = {'title': email_list.title})
        self.flash_messages.add(msg, type='success')
        return HTTPFound(location=self.request.resource_url(self.request.root))


def includeme(config):
    config.add_route('confirm_subscription', '/cf/{email_list}/{list_subscriber}/{token}')
    config.scan(__name__)
