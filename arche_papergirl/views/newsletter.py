# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.interfaces import IFile
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_EDIT
from arche.views.file import AddFileForm
from arche.views.base import BaseForm
from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.view import view_defaults
from zope.interface.interfaces import ComponentLookupError

from arche_papergirl import _
from arche_papergirl.fanstatic_lib import paper_manage
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.interfaces import ISectionPopulatorUtil
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl.utils import deliver_newsletter
from arche_papergirl.utils import send_to_list
from arche_papergirl.utils import work_through_queue
from arche_papergirl.utils import render_newsletter
from arche_papergirl.security import PERM_ADD_NEWSLETTER_SECTION


@view_defaults(context = INewsletter, permission = PERM_EDIT)
class NewsletterView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/newsletter.pt')
    def view(self):
        paper_manage.need()
        #Autoneed fetches css/js dependencies if we initialize the forms here
        InlineAddFileForm(self.context, self.request)()
        sections = [x for x in self.context.values() if INewsletterSection.providedBy(x)]
        attachments = [x for x in self.context.values() if IFile.providedBy(x)]
        send_test_form = SendTestSubForm(self.context, self.request)()
        to_list_form = SendToListSubForm(self.context, self.request)()
        for subform in (send_test_form, to_list_form):
            if isinstance(subform, Exception):
                if isinstance(subform, HTTPFound):
                    return subform
                raise subform
        return {'sections': sections,
                'attachments': attachments,
                'send_test_form': send_test_form['form'],
                'send_to_list_form': to_list_form['form']}

    def get_populators(self):
        return self.request.registry.getAllUtilitiesRegisteredFor(ISectionPopulatorUtil)

    @view_config(name = 'reset_queue')
    def reset_queue(self):
        self.context._queue.clear()
        self.context._uid_to_status.clear()
        return HTTPFound(location=self.request.resource_url(self.context))

    # @view_config(name = 'manual_send.json', renderer='json')
    # def manual_send(self):
    #     subscriber, email_list, tpl = _next_objs(self.context, self.request)
    #     deliver_newsletter(self.request, self.context, subscriber, email_list, tpl)
    #     return {'status': 'sent',
    #             'pending': self.context.queue_len}

    @view_config(name = 'send_celery.json', renderer='json')
    def celery_send(self):
        res = work_through_queue(self.request, self.context)
        url = self.request.route_url('task_status', task_id = res.task_id)
        return {'task_id': res.task_id,
                'status_url': url}

    @view_config(name = 'task_terminate')
    def task_terminate(self):
        if self.context.task_id:
            from arche_papergirl.tasks import work_through_queue
            res = work_through_queue.AsyncResult(self.context.task_id)
            res.revoke(terminate=True)
            for cres in res.children:
                cres.revoke(terminate=True)
            self.context.task_id = None
            self.flash_messages.add(_("Task(s) terminated"), type='warning')
        else:
            self.flash_messages.add(_("Not running"), type='danger')
        back_url = self.request.resource_url(self.context)
        return HTTPFound(location=back_url)

    @view_config(name = 'status.json', renderer = 'json')
    def newsletter_status(self):
        results = self.context.get_status()
        results['running_task_id'] = self.context.task_id
        return results

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


class SendTestSubForm(BaseForm):
    schema_name = "send_test"
    type_name = "Newsletter"
    title = _("Send test email")
    formid = 'deform-test-email'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_test', title = _("Send")),)

    @property
    def form_options(self):
        options = super(SendTestSubForm, self).form_options
        options['action'] = self.request.resource_url(self.context, anchor='test_tab')
        return options

    def send_test_success(self, appstruct):
        email_template = self.request.resolve_uid(self.context.email_template)
        email_list = self.request.content_factories['EmailList'](
            title = self.request.localizer.translate(_("(Test list title)"))
        )
        for email in appstruct['emails']:
            subscriber = self.request.content_factories['ListSubscriber'](
                email = email,
                token = "TEST",
            )
            deliver_newsletter(self.request, self.context, subscriber, email_list, email_template)
        msg = _("Sent ${num} test emails",
                mapping = {'num': len(appstruct['emails'])})
        self.flash_messages.add(msg, type='success')
        return HTTPFound(location=self.request.resource_url(self.context))


class SendToListSubForm(BaseForm):
    schema_name = "send_to_lists"
    type_name = "Newsletter"
    title = _("Send to list")
    formid = 'deform-to-lists'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_to_lists', title = _("Send")),)

    def send_to_lists_success(self, appstruct):
        async_res = send_to_list(self.request, self.context, appstruct['recipient_list'])
        return HTTPFound(location=self.request.resource_url(self.context, query = {'queue_id': async_res.id}))


@view_config(context=INewsletterSection,
             name='populate',
             permission=PERM_EDIT,
             renderer='arche:templates/form.pt')
class PopulateSectionForm(BaseForm):
    type_name = 'NewsletterSection'
    use_ajax = True
    buttons = (BaseForm.button_add, BaseForm.button_cancel)

    @property
    def populator(self):
        name = self.request.GET.get('pop', '')
        try:
            return self.request.registry.getUtility(ISectionPopulatorUtil, name = name)
        except ComponentLookupError:
            raise HTTPNotFound("No populator called %r" % name)

    def get_schema(self):
        return self.populator.get_schema(self.context, self.request)

    def add_success(self, appstruct):
        #Store populator info for a possible rollback
        self.context.populator_appstruct = appstruct
        self.context.populator_name = self.populator.name
        html = self.populator.render(self.context, self.request, **appstruct)
        self.context.update(body = html)
        return self.relocate_response(self.request.resource_url(self.context.__parent__, anchor=self.context.uid),
                                      msg = self.default_success)

    def cancel(self, *args):
        return self.relocate_response(self.request.resource_url(self.context), msg = self.default_cancel)
    cancel_success = cancel_failure = cancel


@view_config(context=INewsletterSection,
             name='reset',
             permission=PERM_EDIT)
class ResetSectionView(BaseView):

    def __call__(self):
        if not self.context.populator_name:
            raise HTTPForbidden("No populator info stored")
        populator = self.request.registry.getUtility(ISectionPopulatorUtil, name=self.context.populator_name)
        html = populator.render(self.context, self.request, **self.context.populator_appstruct)
        self.context.update(body = html)
        return self.relocate_response(self.request.resource_url(self.context.__parent__, anchor=self.context.uid),
                                      msg = _("Reset to initial state"))


@view_config(context = INewsletter,
             name = 'quick_add',
             permission = PERM_ADD_NEWSLETTER_SECTION)
class QuickAddSection(BaseView):

    def __call__(self):
        obj = self.request.content_factories['NewsletterSection']()
        self.context[obj.uid] = obj
        return HTTPFound(self.request.resource_url(self.context, anchor=obj.uid))


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


def includeme(config):
    config.scan(__name__)
