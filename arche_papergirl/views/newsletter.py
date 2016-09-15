# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.interfaces import IFile
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_EDIT
from arche.views.base import BaseView
from arche.views.base import DefaultAddForm
from arche.views.base import BaseForm
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.view import view_defaults
from arche.views.file import AddFileForm

from arche_papergirl import _
from arche_papergirl.exceptions import AlreadyInQueueError
from arche_papergirl.fanstatic_lib import paper_manage
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl.utils import deliver_newsletter
from arche_papergirl.utils import render_newsletter


@view_defaults(context = INewsletter, permission = PERM_EDIT)
class NewsletterView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/newsletter.pt')
    def view(self):
        paper_manage.need()
        #Autoneed fetches css/js dependencies if we initialize the forms here
        InlineAddFileForm(self.context, self.request)()
        AddSectionForm(self.context, self.request)()
        sections = [x for x in self.context.values() if INewsletterSection.providedBy(x)]
        attachments = [x for x in self.context.values() if IFile.providedBy(x)]
        single_form = SendSingleSubForm(self.context, self.request)()
        preview_form = PreviewSubForm(self.context, self.request)()
        to_list_form = SendToListSubForm(self.context, self.request)()
        for subform in (single_form, preview_form, to_list_form):
            if isinstance(subform, Exception):
                if isinstance(subform, HTTPFound):
                    return subform
                raise subform
        return {'sections': sections,
                'attachments': attachments,
                'send_single_form': single_form['form'],
                'preview_form': preview_form['form'],
                'send_to_list_form': to_list_form['form']}

    @view_config(name = 'manual_send.json', renderer='json')
    def manual_send(self):
        subscriber, email_list, tpl = _next_objs(self.context, self.request)
        deliver_newsletter(self.request, self.context, subscriber, email_list, tpl)
        return {'status': 'sent',
                'pending': self.context.queue_len}

    @view_config(name = 'send_details', renderer = 'arche_papergirl:templates/send_details.pt')
    def send_details(self):
        email_lists = {}
        results = []
        for uid in self.context.recipient_uids():
            status, list_uid, timestamp = self.context.get_uid_status(uid)
            if status == 0:
                status_text = _("Delivered")
            if status < 0:
                status_text = _("Error (${err_num})",
                                mapping = {'err_num': status})
            if status > 0:
                status_text = _("In queue (${num})",
                                mapping = {'num': status})
            row = {'subs': self.request.resolve_uid(uid),
                   'status': status_text,
                   'email_list': email_lists.setdefault(list_uid, self.request.resolve_uid(list_uid)),
                   'timestamp': timestamp,
                   }
            results.append(row)
        return {'details': results}


@view_config(context=INewsletter, permission=PERM_EDIT, name='preview.html')
def preview_view(context, request):
    tpl = request.resolve_uid(context.email_template)
    if not IEmailListTemplate.providedBy(tpl):
        raise HTTPNotFound("Specified template not found")
    subscriber = request.content_factories['ListSubscriber'](
        email="noreply@betahaus.net",
        token="TEST",
    )
    email_list = request.content_factories['EmailList'](
        title=request.localizer.translate(_("(Test list title)"))
    )
    return Response(render_newsletter(request, context, subscriber, email_list, tpl))


class SendSingleSubForm(BaseForm):
    schema_name = "send_single"
    type_name = "Newsletter"
    title = _("Send to single recipient")
    formid = 'deform-send-single'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_single', title = _("Send")),)

    @property
    def form_options(self):
        options = super(SendSingleSubForm, self).form_options
        options['action'] = self.request.resource_url(self.context, anchor='test_tab')
        return options

    def send_single_success(self, appstruct):
        email_template = self.request.resolve_uid(self.context.email_template)
        subscriber = self.request.content_factories['ListSubscriber'](
            email = appstruct['email'],
            token = "TEST",
        )
        email_list = self.request.content_factories['EmailList'](
            title = self.request.localizer.translate(_("(Test list title)"))
        )
        deliver_newsletter(self.request, self.context, subscriber, email_list, email_template)
        self.flash_messages.add(self.default_success, type='success')
        return HTTPFound(location=self.request.resource_url(self.context))


class PreviewSubForm(BaseForm):
    schema_name = "preview"
    type_name = "Newsletter"
    title = _("Preview")
    formid = 'deform-preview'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('preview', title = _("Preview")),)

    def preview_success(self, appstruct):
        return HTTPFound(location=self.request.resource_url(self.context, 'preview.html'))


class SendToListSubForm(BaseForm):
    schema_name = "send_to_lists"
    type_name = "Newsletter"
    title = _("Send to list")
    formid = 'deform-to-lists'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_to_lists', title = _("Send")),)

    def send_to_lists_success(self, appstruct):
        list_uid = appstruct['recipient_list']
        found_subs = 0
        already_added_subs = 0
        query = "list_references == '%s' and type_name == 'ListSubscriber'" % list_uid
        for subs in self.catalog_query(query, resolve=True):
            try:
                self.context.add_queue(subs.uid, list_uid)
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
             request_param="content_type=NewsletterSection",
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class AddSectionForm(DefaultAddForm):
    type_name = 'NewsletterSection'
    use_ajax = True

    def save_success(self, appstruct):
        #FIXME: populate from referenced, or create blank
        section_appstruct = {}
        res = super(AddSectionForm, self).save_success(section_appstruct)
        if isinstance(res, HTTPFound) and self.request.is_xhr:
            return self.relocate_response(res.location, msg = "")
        return res

    def cancel(self, *args):
        return  self.relocate_response(self.request.resource_url(self.context), msg = self.default_cancel)
    cancel_success = cancel_failure = cancel


@view_config(context = INewsletter,
             name = 'add',
             request_param="content_type=File",
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class InlineAddFileForm(AddFileForm):
    use_ajax = True

    def save_success(self, appstruct):
        res = super(InlineAddFileForm, self).save_success(appstruct)
        if isinstance(res, HTTPFound) and self.request.is_xhr:
            url = self.request.resource_url(self.context) #To parent instead
            return self.relocate_response(url, msg="")
        return res

    def cancel(self, *args):
        return self.relocate_response(self.request.resource_url(self.context), msg=self.default_cancel)
    cancel_success = cancel_failure = cancel


@view_config(context=INewsletterSection,
             permission = NO_PERMISSION_REQUIRED)
def redirect_to_parent_uid_anchor(context, request):
    url = request.resource_url(context.__parent__, anchor = context.uid)
    return HTTPFound(location = url)


def _next_objs(newsletter, request):
    subscriber_uid, list_uid = newsletter.pop_next()
    if not subscriber_uid:
        return None, None, None
    subscriber = request.resolve_uid(subscriber_uid)
    email_list = request.resolve_uid(list_uid)
    tpl = request.resolve_uid(newsletter.email_template)
    return subscriber, email_list, tpl


def includeme(config):
    config.scan(__name__)
