# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import deform
from arche.security import PERM_VIEW
from arche.views.base import BaseView
from arche_papergirl.fanstatic_lib import paper_manage
from pyramid.view import view_config, view_defaults

from arche_papergirl.interfaces import IListSubscribers
from arche_papergirl import _


@view_defaults(context=IListSubscribers,
               permission=PERM_VIEW)
class ManageListSubscribers(BaseView):

    @view_config(renderer="arche_papergirl:templates/list_subscribers.pt")
    def main(self):
        paper_manage.need()
        return {}

    @view_config(name = 'subscribers.json', renderer='json')
    def subscriber_json(self):
        items = []
        results = {'items': items}
        format_dt = self.request.dt_handler.format_dt
        transl = self.request.localizer.translate
        for obj in self.context.values():
            items.append({'email': obj.email,
                          'list_tags': " ".join([self.get_list_tag(x) for x in obj.list_references]),
                          'created': transl(format_dt(obj.created)),
                          'modified': transl(format_dt(obj.modified)),
                          'uid': obj.uid,
                          'name': obj.__name__})
        return results

    def get_list_tag(self, uid):
        try:
            current = self._list_tags
        except AttributeError:
            current = self._list_tags = {}
        try:
            return current[uid]
        except KeyError:
            obj = self.request.resolve_uid(uid)
            current[uid] = """<a href="">{title}</a>""".format(title=obj.title)
            return current[uid]


def includeme(config):
    config.scan(__name__)
