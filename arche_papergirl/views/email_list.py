# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.security import PERM_VIEW
from arche.views.base import BaseView
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl.interfaces import IEmailList


@view_defaults(context=IEmailList,
               permission=PERM_VIEW)
class EmailListView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/email_list.pt')
    def main(self):
        query = "list_references == '%s'" % self.context.uid
        count = self.root.catalog.query(query, )[0].total
        return {'list_subscribers': count}


def includeme(config):
    config.scan(__name__)
