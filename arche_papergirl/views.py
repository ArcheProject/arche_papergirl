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
        query = "subscribed_lists == '%s' and type_name == 'ListSubscriber'" % list_uid
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


# @view_config(context=IListSubscribers,
#                permission=PERM_VIEW,
#                name='view',
#                renderer = 'arche:templates/form.pt')
# #FIXME: Check permission
# class ListSubscribersView(BaseForm):
#     schema_name = "search"
#     type_name = "ListSubscribers"
#     #title = _("Update subscribers")
#     formid = 'deform-search-subscribers'
#     #Important - make sure button names are unique since all forms will execute otherwise
#     buttons = (deform.Button('search', title = _("Search")),
#                deform.Button('cancel', title = _("Cancel")),)
#     use_ajax = True
#
#     ajax_options = """
#         {success:
#           function (rText, sText, xhr, form) {
#             console.log(rText);
#             //debugger;
#             arche.load_flash_messages();
#             /*
#             var loc = xhr.getResponseHeader('X-Relocate');
#             if (loc) {
#               document.location = loc;
#             };
#             */
#            }
#         }
#     """
#
#     def search_success(self, appstruct):
#         print appstruct
#         #self.flash_messages.add('blabla')
#         return _redirect_or_remove(self)
#
#     def cancel(self, *args):
#         return _redirect_or_remove(self)
#     cancel_success = cancel_failure = cancel


@view_config(context=IListSubscriber,
             name='unsubscribe',
             permission=NO_PERMISSION_REQUIRED,
             renderer='arche:templates/form.pt')
class ListSubscriberManage(BaseForm):
    type_name = 'ListSubscriber'
    schema_name = 'manage_unsubscribe'

    buttons = (deform.Button('unsubscribe', title = _("Unsubscribe"), css_class='btn-danger'),)

    def __init__(self, context, request):
        super(ListSubscriberManage, self).__init__(context, request)
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


@view_defaults(context=IPostOffice,
               permission=PERM_VIEW)
class PostOfficeView(BaseView):

    @view_config(renderer='arche_papergirl:templates/postoffice.pt')
    def view(self):
        paper_manage.need()
        #To make autoneed need stuff :)
        UpdateSubscribersForm(self.context, self.request)()
        response = {}
        path = resource_path(self.context)
        response['email_lists'] = self.catalog_query(
            "type_name == 'EmailList' and path == '%s'" % path,
            resolve=True,
            sort_index='sortable_title'
        )
        response['list_templates'] = self.catalog_query(
            "type_name == 'EmailListTemplate' and path == '%s'" % path,
            resolve=True,
            sort_index='sortable_title'
        )
        response['latest_newsletters'] = self.catalog_query(
            "type_name == 'Newsletter' and path == '%s'" % path,
            resolve=True,
            sort_index='created',
            limit = 10,
            reverse=True
        )
        return response


@view_config(context=IPostOffice,
            permission=PERM_EDIT,
            name = 'update_subscribers',
             renderer = 'arche:templates/form.pt')
class UpdateSubscribersForm(BaseForm):
    schema_name = "update"
    type_name = "ListSubscriber"
    title = _("Update subscribers")
    formid = 'deform-update-subscribers'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('add', title = _("Add")),
               deform.Button('remove', title = _("Remove"), css_class = "btn btn-danger"),
               deform.Button('cancel', title = _("Cancel")),)
    use_ajax = True

    ajax_options = """
        {success:
          function (rText, sText, xhr, form) {
            console.log(rText);
            //debugger;
            arche.load_flash_messages();
            /*
            var loc = xhr.getResponseHeader('X-Relocate');
            if (loc) {
              document.location = loc;
            };
            */
           }
        }
    """

    # @property
    # def form_options(self):
    #     options = super(UpdateSubscribersForm, self).form_options
    #     #options['action'] = self.request.resource_url(self.context, 'add_subscriber')
    #     print "form action:", options['action']
    #     return options

    def add_success(self, appstruct):
        #obj = self.request.content_factories['ListSubscriber'](email = appstruct['email'])
        #self.context.subscribers[obj.uid] = obj
        for email in appstruct['emails'].splitlines():
            if not email:
                continue
            subs = self.context.subscribers.email_to_subs(email)
            if subs is None:
                subs = self.request.content_factories['ListSubscriber'](email = email)
                self.context.subscribers[subs.uid] = subs
            subs.add_lists(appstruct['lists'])
        self.flash_messages.add('Added')
        return _redirect_or_remove(self)

    def remove_success(self, appstruct):
        for email in appstruct['email'].splitlines():
            if not email:
                continue
            subs = self.context.subscribers.email_to_subs(email)
            if subs is None:
                #Don't create if they don't exist!
                continue

            subs.remove_lists(appstruct['lists'])
        print appstruct
        self.flash_messages.add('remove success')
        return _redirect_or_remove(self)

    def cancel(self, *args):
        return _redirect_or_remove(self)
    cancel_success = cancel_failure = cancel


def _redirect_or_remove(formview):
    if formview.request.is_xhr:
        return Response("""
        <script>$('#{}').remove();</script>""".format(formview.formid))
    return HTTPFound(location=formview.request.resource_url(formview.context))


def includeme(config):
    config.add_route('confirm_subscription', '/cf/{email_list}/{list_subscriber}/{token}')
    config.scan(__name__)
