from arche.security import PERM_VIEW
from chameleon.zpt.template import PageTemplate
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path

from arche_papergirl.interfaces import IEmailList, IPostOffice
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import INewsletter


def deliver_newsletter(newsletter, request):
    subscriber_uid, list_uid, tpl_uid = newsletter.pop_next()
    if not subscriber_uid:
        # Nothing to do - status?
        return {}
    subscriber = request.resolve_uid(subscriber_uid)
    # assert IListSubscriber.providedBy(subscriber)
    email_list = request.resolve_uid(list_uid)
    tpl = request.resolve_uid(tpl_uid)
    # FIXME: Check subscriber active?
    html = render_newsletter(request, newsletter, subscriber, email_list, tpl)
    subject = newsletter.title
    request.send_email(
        subject,
        [subscriber.email],
        html,
        send_immediately=True
    )


def render_newsletter(request, newsletter, subscriber, email_list, email_template, **kwargs):
    assert INewsletter.providedBy(newsletter)
    assert IListSubscriber.providedBy(subscriber)
    assert IEmailList.providedBy(email_list)
    assert IEmailListTemplate.providedBy(email_template)
    page_tpl = PageTemplate(email_template.body)
    tpl_values = dict(
        newsletter = newsletter,
        subscriber = subscriber,
        email_list = email_list,
        request = request,
        **kwargs
    )
    #FIXME: Encoding, translation?
    return page_tpl.render(**tpl_values)


def get_po_objs(context, request, type_name, perm = PERM_VIEW, sort_index = 'sortable_title', **kw):
    """
    :param context: A context within a PostOffice context
    :param request:
    :param type_name: Which type to fetch
    :return: iterator with EmailListTemplate objects
    """
    po = find_interface(context, IPostOffice)
    path = resource_path(po)
    query = "type_name == '%s'" % type_name
    query += "path == '%s'" % path
    docids = request.root.catalog.query(query, sort_index = sort_index, **kw)[1]
    return request.resolve_docids(docids, perm = perm)
