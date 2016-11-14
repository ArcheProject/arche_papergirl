from logging import getLogger

from celery import chord
from celery import group
from pyramid_celery import celery_app as app

from arche_papergirl.exceptions import AlreadyInQueueError
from arche_papergirl.interfaces import INewsletter
from arche_papergirl.interfaces import IPostOffice
from arche_papergirl.utils import deliver_newsletter


logger = getLogger(__name__)


@app.task(bind=True, default_retry_delay=3, max_retries=3)
def update_subscribers(self, request = None, context = None,
                       emails_text = "", emails_lists = (),
                       action = '', **kw):
    assert IPostOffice.providedBy(context), "context must be PostOffice object"
    valid_actions = ('add_lists', 'remove_lists')
    if action not in valid_actions:
        raise Exception("No such action: %s" % action)
    for email in emails_text.splitlines():
        if not email:
            continue
        subs = context.subscribers.email_to_subs(email)
        if subs is None:
            subs = request.content_factories['ListSubscriber'](email=email)
            context.subscribers[subs.uid] = subs
        meth = getattr(subs, action)
        meth(emails_lists)


@app.task(bind=True, default_retry_delay=3, max_retries=3)
def add_list_to_queue(self, list_uid, request = None, context = None, **kw):
    """
    :param context: Must be a Newsletter
    :param list_uid: UID of the list we want to send to
    :return:
    """
    assert INewsletter.providedBy(context)
    query = "list_references == '%s' and type_name == 'ListSubscriber'" % list_uid
    docids = request.root.catalog.query(query)[1]
    found_subs = 0
    already_added_subs = 0
    for subs in request.resolve_docids(docids):
        try:
            context.add_queue(subs.uid, list_uid)
            found_subs += 1
        except AlreadyInQueueError:
            already_added_subs += 1
    logger.debug("Found subscribers: %s. Already added subscribers: %s", found_subs, already_added_subs)
    from time import sleep
    #sleep(3)


@app.task(bind=True, default_retry_delay=20, max_retries=2)
def work_through_queue(self, request = None, context = None, **kw):
    """
    :param request: Pyramids request object.
    :param context: Newsletter object
    Go through all the users that should be queued for delivery and create subtasks
    to do each. The relevant part to track will be found at <AsyncResult>.children[0],
    which will contained the grouped subtasks. However, that won't exist until the task has
    actually started :)
    """
    assert INewsletter.providedBy(context)
    context.task_id = self.request.id

    #group expects something with a len so don't use a generator!
    to_email = []
    for (queue_order, subscriber_uid, list_uid) in context.iter_queue():
    #for x in range(30):
        to_email.append(
            send_to_user.s(
            #slow_task.s(
                context_uid=context.uid,
                authenticated_userid=request.authenticated_userid,
                subscriber_uid=subscriber_uid,
                list_uid=list_uid,
                queue_order=queue_order,
            )
        )
    grouped_tasks = group(to_email)
    chord(
        grouped_tasks,
        remove_context_task_id.si(
            context_uid=context.uid,
            authenticated_userid=request.authenticated_userid,
        )
    ).apply_async()


@app.task(bind=True, default_retry_delay=1, max_retries=15, ignore_result=True)
def remove_context_task_id(self, request = None, context = None, **kw):
    context.task_id = None


@app.task(bind=True)
def send_to_user(self, request = None, context = None,
                 subscriber_uid = '', list_uid = '',
                 queue_order = None, **kw):
    assert INewsletter.providedBy(context)
    subscriber = request.resolve_uid(subscriber_uid)
    email_list = request.resolve_uid(list_uid)
    current_status = context.get_uid_status(subscriber_uid)
    if not current_status:
        logger.warn("'send_to_user' tried to add %s, and that subscriber_uid is not in the queue." % subscriber_uid)
        return
    if current_status[0] == 0:
        logger.warn("newsletter %s already delivered to subscriber %s." % (subscriber_uid, context.uid))
        return
    tpl = request.resolve_uid(context.email_template)
    #FIXME: Check mailer problem and attach that to retry? Retries for celery fail when testing
    deliver_newsletter(request, context, subscriber, email_list, tpl)
    context.completed(queue_order)
