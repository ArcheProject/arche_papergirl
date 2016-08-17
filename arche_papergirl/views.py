import deform
from arche.security import PERM_EDIT, PERM_VIEW
from arche.security import NO_PERMISSION_REQUIRED
from arche.views.base import BaseView, DefaultAddForm, BaseForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.models import render_newsletter
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl.interfaces import IEmailList
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.fanstatic_lib import paper_manage


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
        email_list = self.request.resolve_uid( self.request.GET.get('list_uid', '') )
        subscriber = self.context.process_next(self.request, email_list.uid)
        if not subscriber:
            #Nothing to do - status?
            return {}
        assert IListSubscriber.providedBy(subscriber)
        #FIXME: Check subscriber active?
        html = render_newsletter(self.request, self.context, subscriber, email_list)
        subject = self.context.title
        self.request.send_email(subject,
                                [subscriber.email],
                                html,
                                send_immediately = True)
        return {'status': 'sent',
                'uid': subscriber.uid,
                'list_uid': email_list.uid,
                'pending': len(self.context.pending[email_list.uid])}


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
        email_list = self.request.resolve_uid(appstruct['recipient_list'])
        ls_fact = self.request.content_factories['ListSubscriber']
        subscriber = ls_fact(email = appstruct['email'],
                             subscribe_token = "TEST_SUBSCRIBE",
                             unsubscribe_token = "TEST_UNSUBSCRIBE")
        html = render_newsletter(self.request, self.context, subscriber, email_list)
        subject = self.context.title
        self.request.send_email(subject,
                                [appstruct['email']],
                                html,
                                send_immediately = True)
        self.flash_messages.add(self.default_success, type='success')
        return HTTPFound(location=self.request.resource_url(self.context))


class SendToListSubForm(BaseForm):
    schema_name = "send_to_list"
    type_name = "Newsletter"
    title = _("Send to list")
    formid = 'deform-to-list'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_to_list', title = _("Send")),)
    #use_ajax = True

    def send_to_list_success(self, appstruct):
        email_list = self.request.resolve_uid(appstruct['recipient_list'])
        self.context.add_to_list(email_list)
        msg = _("mail_queued_notice",
                default="Mail added to queue")
        self.flash_messages.add(msg, type='success')
        #FIXME: Figure out if a more sane mailer is installed?
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


@view_defaults(context=IEmailList,
               permission=PERM_VIEW)
class EmailListView(BaseView):

    @reify
    def current_subsciber_emails(self):
        return tuple(self.context.get_emails())

    @view_config(name='view', renderer='arche_papergirl:templates/email_list.pt')
    def main(self):
        return {'emails': self.current_subsciber_emails}

    @view_config(name='pending_confirm', renderer='arche_papergirl:templates/confirm_subscription.pt')
    def confirm_subscription(self):
        return {}


@view_config(context = IEmailList,
             name = 'request',
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class RequestSubscriptionChange(BaseForm):
    schema_name = "request"
    type_name = "EmailList"
    buttons = (deform.Button('subscribe', title=_("Subscribe")),
               deform.Button('unsubscribe', title=_("Unsubscribe")),)

    def subscribe_success(self, appstruct):
        try:
            obj = self.context.create_subscriber(appstruct['email'])
        except ValueError:
            msg = _("Already in list")
            self.flash_messages.add(msg, type='danger')
            return HTTPFound(location=self.request.url)
        url = self.request.resource_url(obj, 'subscribe', obj.subscribe_token)
        html = self.render_template("arche_papergirl:templates/mail_subscribe.pt", context = self.context, url = url)
        subject = _("${title} subscription request",
                    mapping = {'title': self.context.title})
        self.request.send_email(subject,
                                [appstruct['email']],
                                html,
                                send_immediately = True)
        return HTTPFound(location=self.request.resource_url(self.context, 'pending_confirm'))

    def unsubscribe_success(self, appstruct):
        obj = self.context.find_subscriber(appstruct['email'])
        if obj and obj.active:
            url = self.request.resource_url(obj, 'unsubscribe', obj.unsubscribe_token)
            html = self.render_template("arche_papergirl:templates/mail_unsubscribe.pt", context = self.context, url = url)
            subject = _("unsubscribe ${title}",
                        mapping = {'title': self.context.title})
            self.request.send_email(subject,
                                    [appstruct['email']],
                                    html,
                                    send_immediately = True)
            return HTTPFound(location=self.request.resource_url(obj, 'unsubscribe'))
        else:
            msg = _("no_active_subscriber_found",
                    default="No active subscriber with that email address found.")
            self.flash_messages.add(msg, type='danger')
            return HTTPFound(location=self.request.url)


@view_defaults(context=IListSubscriber,
               permission=NO_PERMISSION_REQUIRED)
class ListSubscriberView(BaseView):

    @property
    def token(self):
        try:
            return self.request.subpath[0]
        except IndexError:
            return

    @view_config(name='subscribe', renderer='arche_papergirl:templates/subscription_confimed.pt')
    def subscribe(self):
        if self.token and self.token == self.context.subscribe_token:
            self.context.set_active(True)
            return {}
        raise HTTPBadRequest(_("Token doesn't match"))

    @view_config(name='unsubscribe', renderer='arche_papergirl:templates/unsubscribe_notice.pt')
    def unsubscribe(self):
        if self.token and self.token == self.context.unsubscribe_token:
            self.context.set_active(False)
            return {'subscribe_url': self.request.resource_url(self.context, 'subscribe', self.context.subscribe_token)}
        raise HTTPBadRequest(_("Token doesn't match"))

def includeme(config):
    config.scan(__name__)
