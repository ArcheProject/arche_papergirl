# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import PERM_EDIT
from arche.security import PERM_VIEW
from arche.views.base import BaseForm
from arche.views.base import BaseView
from arche_papergirl.tasks import update_subscribers
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.fanstatic_lib import paper_manage
from arche_papergirl.interfaces import IPostOffice


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
            limit=5,
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
            arche.load_flash_messages();
           }
        }
    """

    def add_success(self, appstruct):
        self.request.add_task(update_subscribers, self.context,
                              emails_text = appstruct['emails'],
                              emails_lists = appstruct['lists'],
                              action = 'add_lists')
        self.flash_messages.add(_("Subscribers will be added shortly when a worker is ready"))
        return _redirect_or_remove(self)

    def remove_success(self, appstruct):
        self.request.add_task(update_subscribers, self.context,
                              emails_text = appstruct['emails'],
                              emails_lists = appstruct['lists'],
                              action = 'remove_lists')
        self.flash_messages.add(_("Update will commence as soon as a worker is ready."))
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
    config.scan(__name__)
