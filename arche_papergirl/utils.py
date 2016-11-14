from __future__ import unicode_literals

import re
from arche.interfaces import IFile, IBlobs, IFlashMessages
from arche.security import PERM_VIEW
from chameleon.zpt.template import PageTemplate
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Attachment
from premailer import Premailer
from pyramid.path import AssetResolver

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
        html,
        sender=newsletter.sender,
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
    html = page_tpl.render(**tpl_values)
    filenames = request.registry.settings.get('papergirl.mail_css', ())
    if filenames:
        html = inject_css_from_files(email_template, filenames, html,
                                     debug = request.registry.settings.get('arche.debug', False))
    if email_template.use_premailer:
        html = Premailer(html, base_url=request.host_url, keep_style_tags=True).transform()
    return html


_INJECT_TPL = """
<style type="text/css">
%s
</style>
"""

def inject_css_from_files(email_template, filenames, html, debug = False):
    css_out = ""
    resolver = AssetResolver()
    for relpath in filenames:
        resolved = resolver.resolve(relpath)
        abspath = resolved.abspath()
        if debug:
            css_out += "\n/* START %s */\n\n" % relpath
        with open(abspath, 'r') as fb:
            css_out += fb.read().decode('utf-8')
        if debug:
            css_out += "\n\n/* END %s */\n\n" % relpath
    out = _INJECT_TPL % css_out

    #Find the head tag
    pattern = re.compile("<head[^>]*>", flags=re.IGNORECASE)
    head_tag_list = pattern.findall(html)
    if len(head_tag_list) != 1:
        raise ValueError("Head tag not found")
    out = "%s\n%s" % (head_tag_list[0], out)
    return html.replace(head_tag_list[0], out)


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


def work_through_queue(request, newsletter):
    fm = IFlashMessages(request)
    if request.registry.settings.get('papergirl.use_celery', False):
        from arche_papergirl.tasks import work_through_queue
        fm.add("Queue send started, reload page to show progress.")
        return request.add_task(work_through_queue, newsletter)
        #The actual group-task will be within children
        #return res.children[0]
    else:
        raise Exception("Celery not found")


def send_to_list(request, newsletter, list_uid):
    fm = IFlashMessages(request)
    if request.registry.settings.get('papergirl.use_celery', False):
        from arche_papergirl.tasks import add_list_to_queue
        async_res = request.add_task(add_list_to_queue, newsletter, list_uid)
        fm.add("Delegated to queue")
        return async_res
    else:
        #Should we keep support for not using celery?
        raise Exception("Celery not found")
