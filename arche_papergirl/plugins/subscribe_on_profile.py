# Add a proxy attribute to User that delegates settings to email lists

import colander
import deform
from arche.interfaces import IObjectAddedEvent
from arche.interfaces import IObjectUpdatedEvent
from arche.interfaces import ISchemaCreatedEvent
from arche.interfaces import IUser
from arche.schemas import FinishRegistrationSchema
from arche.schemas import UserSchema
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface

from arche_papergirl.interfaces import IPostOffice
from arche_papergirl.schemas import EmailListSchema
from arche_papergirl import _


def _get_papergirl_subscriptions(self):
    """ Return the UIDs of all lists subscribed to """
    # FIXME: Make sure sure user email is validated before adding the widget?
    request = get_current_request()
    query = "type_name == 'ListSubscriber' and email == '%s'" % self.email
    docids = request.root.catalog.query(query)[1]
    results = set()
    for obj in request.resolve_docids(docids):
        results.update(obj.list_references)
    return results


def _set_papergirl_subscriptions(self, value):
    if not self.email:
        #Deferred setting of values to be picked up later on. See _handle_deferred_add
        self._v_deferred_papergirl_list_uids = value
        return
    current_list_uids = self._papergirl_list_subscriptions
    request = get_current_request()
    for el in get_valid_lists(request):
        po = find_interface(el, IPostOffice)
        if el.uid in value and el.uid not in current_list_uids:
            #Added
            subs = po.subscribers.email_to_subs(self.email)
            if subs is None:
                subs = request.content_factories['ListSubscriber'](email=self.email, )
                po.subscribers[subs.uid] = subs
            subs.add_lists(el.uid)
            #Removed, but may not exist in that post office
        elif el.uid not in value and el.uid in current_list_uids:
            subs = po.subscribers.email_to_subs(self.email)
            subs.remove_lists(el.uid)


def get_valid_lists(request=None):
    """ Get lists to show without permission check. """
    if request is None:
        request = get_current_request()
    cq = request.root.catalog.query
    for po in request.resolve_docids(cq("type_name == 'PostOffice'")[1], perm=None):
        for el in po.get_email_lists():
            if el.subscribe_on_profile:
                yield el


def _subscriber_subscribe_on_profile(schema, event):
    valid_lists = []
    for obj in get_valid_lists(event.request):
        valid_lists.append(obj)
    if not valid_lists:
        return
    values = [(obj.uid, obj.title) for obj in valid_lists]
    if event.context.type_name != 'User':
        title = _("Do you want to Subscribe to email lists?")
    else:
        title = _("Your subscriptions")
    schema.add(
        colander.SchemaNode(
            colander.Set(),
            title = title,
            name = '_papergirl_list_subscriptions',
            widget = deform.widget.CheckboxChoiceWidget(values = values)
        )
    )


def _list_option_for_profile(schema, event):
    schema.add(colander.SchemaNode(
        colander.Bool(),
        name='subscribe_on_profile',
        title=_("Show this list as a subscription option when a user registers or edits their profile?"),
    ))


def _handle_deferred_add(user, event):
    if hasattr(user, '_v_deferred_papergirl_list_uids'):
        user._papergirl_list_subscriptions = user._v_deferred_papergirl_list_uids
        delattr(user, '_v_deferred_papergirl_list_uids')


def includeme(config):
    from arche.api import User
    User._papergirl_list_subscriptions = property(_get_papergirl_subscriptions, _set_papergirl_subscriptions)
    #Subscriber for adjusting lists
    config.add_subscriber(_handle_deferred_add, [IUser, IObjectUpdatedEvent])
    config.add_subscriber(_handle_deferred_add, [IUser, IObjectAddedEvent])
    #Inject subscription options
    config.add_subscriber(_subscriber_subscribe_on_profile, [FinishRegistrationSchema, ISchemaCreatedEvent])
    config.add_subscriber(_subscriber_subscribe_on_profile, [UserSchema, ISchemaCreatedEvent])
    config.add_subscriber(_list_option_for_profile, [EmailListSchema, ISchemaCreatedEvent])
