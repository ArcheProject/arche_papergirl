from arche.interfaces import IFile, IBlobs
from arche.security import PERM_VIEW
from chameleon.zpt.template import PageTemplate
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Attachment
from premailer import transform

from arche_papergirl.interfaces import IEmailList, IPostOffice
from arche_papergirl.interfaces import IEmailListTemplate
from arche_papergirl.interfaces import IListSubscriber
from arche_papergirl.interfaces import INewsletter


def deliver_newsletter(request, newsletter, subscriber, email_list, tpl):
    assert INewsletter.providedBy(newsletter)
    assert IListSubscriber.providedBy(subscriber)
    assert IEmailList.providedBy(email_list)
    assert IEmailListTemplate.providedBy(tpl)
    # FIXME: Check subscriber active?
    html = render_newsletter(request, newsletter, subscriber, email_list, tpl)
    subject = newsletter.subject
    msg = request.compose_email(
        subject,
        [subscriber.email],
        html
    )
    create_attachments(newsletter, msg)
    mailer = get_mailer(request)
    mailer.send_immediately(msg)
    return msg


def create_attachments(newsletter, msg):
    for obj in newsletter.values():
        if IFile.providedBy(obj):
            with IBlobs(obj)['file'].blob.open() as f:
                attach_data = f.read()
                attachment = Attachment(obj.filename, obj.mimetype, attach_data)
                msg.attach(attachment)


def render_newsletter(request, newsletter, subscriber, email_list, email_template, premailer = transform, **kwargs):
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
    html = page_tpl.render(**tpl_values)
    if premailer:
        html = premailer(html, base_url=request.host_url)
    return html


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
    query += " and path == '%s'" % path
    docids = request.root.catalog.query(query, sort_index = sort_index, **kw)[1]
    return request.resolve_docids(docids, perm = perm)


def get_mock_structure(request):
    newsletter = request.content_factories['Newsletter'](
        title='Newsletter Title',
        description='Short intro'
    )
    nl_section = request.content_factories['NewsletterSection'](
        title='First section title',
        body='<p>Body of the first section</p>',
    )
    newsletter['nl_section'] = nl_section
    subscriber = request.content_factories['ListSubscriber'](
        email='testing@betahaus.net'
    )
    email_list = request.content_factories['EmailList']()
    return newsletter, subscriber, email_list
