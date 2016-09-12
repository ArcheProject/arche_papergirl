# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_EDIT
from arche.views.base import BaseView, DefaultAddForm, BaseForm
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.exceptions import AlreadyInQueueError
from arche_papergirl.fanstatic_lib import paper_manage
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl.utils import deliver_newsletter
from arche_papergirl.utils import render_newsletter


@view_defaults(context = INewsletter, permission = PERM_EDIT)
class NewsletterView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/newsletter.pt')
    def view(self):
        paper_manage.need()
        sections = [x for x in self.context.values() if INewsletterSection.providedBy(x)]
        single_form = SendSingleSubForm(self.context, self.request)()
        to_list_form = SendToListSubForm(self.context, self.request)()
        for subform in (single_form, to_list_form):
            if isinstance(subform, Exception):
                if isinstance(subform, HTTPFound):
                    return subform
                raise subform
        return {'sections': sections,
                'send_single_form': single_form['form'],
                'send_to_list_form': to_list_form['form']}

    @view_config(name = 'manual_send.json', renderer='json')
    def manual_send(self):
        deliver_newsletter(self.context, self.request)
        return {'status': 'sent',
                'pending': self.context.queue_len}


class SendSingleSubForm(BaseForm):
    schema_name = "send_single"
    type_name = "Newsletter"
    title = _("Send to single recipient")
    formid = 'deform-send-single'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_single', title = _("Send")),)
    #use_ajax = True

    @property
    def form_options(self):
        options = super(SendSingleSubForm, self).form_options
        options['action'] = self.request.resource_url(self.context, anchor='test_tab')
        return options

    def send_single_success(self, appstruct):
        email_template = self.request.resolve_uid(appstruct['email_template'])
        subscriber = self.request.content_factories['ListSubscriber'](
            email = appstruct['email'],
            token = "TEST",
        )
        email_list = self.request.content_factories['EmailList'](
            title = self.request.localizer.translate(_("(Test list title)"))
        )
        html = render_newsletter(self.request, self.context, subscriber, email_list, email_template)
        subject = self.context.title
        self.request.send_email(subject,
                                [appstruct['email']],
                                html,
                                send_immediately = True)
        self.flash_messages.add(self.default_success, type='success')
        return HTTPFound(location=self.request.resource_url(self.context))


class SendToListSubForm(BaseForm):
    schema_name = "send_to_lists"
    type_name = "Newsletter"
    title = _("Send to list")
    formid = 'deform-to-lists'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_to_lists', title = _("Send")),)
    #use_ajax = True

    def send_to_lists_success(self, appstruct):
        list_uid = appstruct['recipient_list']
        found_subs = 0
        already_added_subs = 0
        query = "list_references == '%s' and type_name == 'ListSubscriber'" % list_uid
        for subs in self.catalog_query(query, resolve=True):
            try:
                self.context.add_queue(subs.uid, list_uid, appstruct['email_template'])
                found_subs += 1
            except AlreadyInQueueError:
                already_added_subs += 1
        msg = _("mail_queued_notice",
                default="Added: ${found_subs} Skipped: ${already_added_subs} (due to already in queue)",
                mapping = {'found_subs': found_subs, 'already_added_subs': already_added_subs})
        type_status = found_subs and 'success' or 'warning'
        self.flash_messages.add(msg, type=type_status)
        return HTTPFound(location=self.request.resource_url(self.context))


@view_config(context = INewsletter,
             name = 'add',
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class AddSectionForm(DefaultAddForm):

    def save_success(self, appstruct):
        #FIXME: populate from referenced, or create blank
        section_appstruct = {}
        return super(AddSectionForm, self).save_success(section_appstruct)


@view_config(context=INewsletterSection,
             permission = NO_PERMISSION_REQUIRED)
def redirect_to_parent_uid_anchor(context, request):
    url = request.resource_url(context.__parent__, anchor = context.uid)
    return HTTPFound(location = url)


def includeme(config):
    config.scan(__name__)