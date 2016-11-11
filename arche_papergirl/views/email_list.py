# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.security import PERM_VIEW
from arche.views.base import BaseView
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl.interfaces import IEmailList
from arche_papergirl.security import PERM_VIEW_SUBSCRIBERS


@view_defaults(context=IEmailList,
               permission=PERM_VIEW)
class EmailListView(BaseView):

    @view_config(name='view', renderer='arche_papergirl:templates/email_list.pt')
    def main(self):
        query = "list_references == '%s'" % self.context.uid
        count = self.root.catalog.query(query)[0].total
        return {'list_subscribers': count, 'can_export': self.request.has_permission(PERM_VIEW_SUBSCRIBERS)}

    @view_config(name='emails.txt', renderer='string',
                 permission=PERM_VIEW_SUBSCRIBERS)
    def emails_txt(self):
        query = "list_references == '%s'" % self.context.uid
        resultset, docids = self.root.catalog.query(query)
        rows = [
            "%s (%s subscribers)" % (self.context.title, resultset.total),
            "="*80
        ]
        for obj in self.request.resolve_docids(docids, perm=None):
            rows.append(obj.email)
        return "\n".join(rows)


def includeme(config):
    config.scan(__name__)
