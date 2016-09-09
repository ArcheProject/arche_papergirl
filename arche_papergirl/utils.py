from chameleon.zpt.template import PageTemplate

from arche_papergirl.interfaces import IEmailList
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
