# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import NO_PERMISSION_REQUIRED
from arche.security import PERM_VIEW
from arche.views.base import BaseView, BaseForm
from arche_papergirl.utils import get_mock_structure, render_newsletter
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config, view_defaults

from arche_papergirl import _
from arche_papergirl.interfaces import IEmailList, IEmailListTemplate
from arche_papergirl.interfaces import IListSubscriber


@view_defaults(context = IEmailListTemplate)
class EmailListTemplateView(BaseView):

    @view_config(name = 'view',
                 permission=PERM_VIEW,
                 renderer = 'arche_papergirl:templates/email_list_template.pt')
    def main(self):
        return {}


@view_config(context = IEmailListTemplate,
             name = 'tpl.html',
             permission=PERM_VIEW)
def tpl_html(context, request):
    newsletter, subscriber, email_list = get_mock_structure(request)
    return Response(render_newsletter(request, newsletter, subscriber, email_list, context))


def includeme(config):
    config.scan(__name__)
