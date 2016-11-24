from __future__ import unicode_literals

import colander
import deform
from arche_papergirl.views.subscription import RequestSubscriptionForm
from pyramid.renderers import render

from arche.portlets import PortletType
from arche import _


@colander.deferred
def subscribe_title(node, kw):
    request = kw['request']
    return request.localizer.translate(_("Subscribe maillist"))


@colander.deferred
def maillist_widget(node, kw):
    values = [('', _("Select..."))]
    request = kw['request']
    query = "type_name == 'EmailList'"
    docids = request.root.catalog.query(query, sort_index = 'sortable_title')[1]
    for obj in request.resolve_docids(docids):
        values.append((obj.uid, obj.title))
    return deform.widget.SelectWidget(values = values)


class SubscribePortletSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
        description = _("Shown in portlet manager"),
        default = subscribe_title,
    )
    mail_list = colander.SchemaNode(
        colander.String(),
        title = _("Which maillist?"),
        widget = maillist_widget,
    )


class SubscribePortlet(PortletType):
    name = "papergirl_subscribe"
    schema_factory = SubscribePortletSchema
    title = _("Subscribe maillist")
    tpl = 'arche_papergirl:templates/subscribe_portlet.pt'

    def render(self, context, request, view, **kwargs):
        settings = self.portlet.settings
        mail_list = request.resolve_uid(settings.get('mail_list', ''), perm=None)
        subs_form = RequestSubscriptionForm(mail_list, request)
        values = {'title': settings.get('title', self.title),
                  'form': subs_form()['form'],
                  'mail_list': mail_list,
                  'portlet': self.portlet}
        return render(self.tpl,
                      values,
                      request = request)


def includeme(config):
    config.add_portlet(SubscribePortlet)
