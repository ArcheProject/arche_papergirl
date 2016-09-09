# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import PERM_EDIT, PERM_VIEW
from arche.security import NO_PERMISSION_REQUIRED
from arche.views.base import BaseView, DefaultAddForm, BaseForm
from arche_papergirl.exceptions import AlreadyInQueueError
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.utils import deliver_newsletter
from arche_papergirl.utils import render_newsletter
from arche_papergirl.interfaces import INewsletter, IPostOffice, IListSubscribers
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.fanstatic_lib import paper_manage


@view_defaults(context=IEmailList,
               permission=PERM_VIEW)
class EmailListView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/email_list.pt')
    def main(self):
        query = "subscribed_lists == '%s'" % self.context.uid
        count = self.root.catalog.query(query, )[0].total
        return {'list_subscribers': count}

    @view_config(name='pending_confirm', renderer='arche_papergirl:templates/confirm_subscription.pt')
    def confirm_subscription(self):
       return {}


# @view_config(context = IEmailList,
#              name = 'request',
#              permission = NO_PERMISSION_REQUIRED,
#              renderer = 'arche:templates/form.pt')
# class RequestSubscriptionChange(BaseForm):
#     schema_name = "request"
#     type_name = "EmailList"
#     buttons = (deform.Button('subscribe', title=_("Subscribe")),
#                deform.Button('unsubscribe', title=_("Unsubscribe")),)
#
#     def subscribe_success(self, appstruct):
#         try:
#             obj = self.context.create_subscriber(appstruct['email'])
#         except ValueError:
#             msg = _("Already in list")
#             self.flash_messages.add(msg, type='danger')
#             return HTTPFound(location=self.request.url)
#         url = self.request.resource_url(obj, 'subscribe', obj.subscribe_token)
#         html = self.render_template("arche_papergirl:templates/mail_subscribe.pt", context = self.context, url = url)
#         subject = _("${title} subscription request",
#                     mapping = {'title': self.context.title})
#         self.request.send_email(subject,
#                                 [appstruct['email']],
#                                 html,
#                                 send_immediately = True)
#         return HTTPFound(location=self.request.resource_url(self.context, 'pending_confirm'))
#
#     def unsubscribe_success(self, appstruct):
#         obj = self.context.find_subscriber(appstruct['email'])
#         if obj and obj.active:
#             url = self.request.resource_url(obj, 'unsubscribe', obj.unsubscribe_token)
#             html = self.render_template("arche_papergirl:templates/mail_unsubscribe.pt", context = self.context, url = url)
#             subject = _("unsubscribe ${title}",
#                         mapping = {'title': self.context.title})
#             self.request.send_email(subject,
#                                     [appstruct['email']],
#                                     html,
#                                     send_immediately = True)
#             return HTTPFound(location=self.request.resource_url(obj, 'unsubscribe'))
#         else:
#             msg = _("no_active_subscriber_found",
#                     default="No active subscriber with that email address found.")
#             self.flash_messages.add(msg, type='danger')
#             return HTTPFound(location=self.request.url)

def includeme(config):
    config.scan(__name__)
