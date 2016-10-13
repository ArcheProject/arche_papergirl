#FIXME:
# def subscribe_on_profile(config):
#     from arche.api import User
#
#     #Subscriber for adjusting lists
#     config.add_subscriber(_update_lists_with_pending_profile_changes, [IUser, IObjectUpdatedEvent])
#     config.add_subscriber(_update_lists_with_pending_profile_changes, [IUser, IObjectAddedEvent])
#
#     #Add a proxy attribute to User that delegates settings to email lists
#     def _get_email_subscriptions(self):
#         #FIXME: Make sure sure user email is validated before adding the widget?
#         request = get_current_request()
#         query = "type_name == 'ListSubscriber' and email == '%s'" % self.email
#         docids = request.root.catalog.query(query)[1]
#         results = set()
#         for obj in request.resolve_docids(docids):
#             results.update(obj.list_references)
#         return results
#
#         # found_lists = set()
#         # if not self.email:
#         #     return found_lists
#         # for obj in _get_valid_lists():
#         #     subscr = obj.find_subscriber(self.email)
#         #     if subscr != None and subscr.active == True:
#         #         found_lists.add(obj.uid)
#         # return found_lists
#     def _set_email_subscriptions(self, value):
#         print "setting pending changes: ", value
#         self._pending_list_changes = frozenset(value)
#     User._email_list_subscriptions = property(_get_email_subscriptions, _set_email_subscriptions)
#
#
# def _update_lists_with_pending_profile_changes(user, event):
#     return
#
#     #FIXME
#     if not user.email or not hasattr(user, '_pending_list_changes'):
#         return
#     if not getattr(event, 'changed', ()) or '_email_list_subscriptions' in event.changed:
#         pending_lists = user._pending_list_changes
#         for obj in _get_valid_lists():
#             subscr = obj.find_subscriber(user.email)
#             if subscr:
#                 #Adjust existing
#                 if subscr.active == False and obj.uid in pending_lists:
#                     subscr.set_active(True)
#                 if subscr.active == True and obj.uid not in pending_lists:
#                     subscr.set_active(False)
#             elif obj.uid in pending_lists and subscr is None:
#                 #Create subscriber
#                 subscr = obj.create_subscriber(user.email)
#                 subscr.set_active(True)
#         delattr(user, '_pending_list_changes')
#
#


#
# def _subscriber_subscribe_on_profile(schema, event):
#     valid_lists = []
#
#     for obj in get_email_lists(event.request):
#         if obj.subscribe_on_profile == True:
#             valid_lists.append(obj)
#
#     if not valid_lists:
#         return
#     values = [(obj.uid, obj.title) for obj in valid_lists]
#     schema.add(colander.SchemaNode(
#         colander.Set(),
#         name = '_email_list_subscriptions',
#         widget = deform.widget.CheckboxChoiceWidget(values = values)
#     ))
#
#
# def _list_option_for_profile(schema, event):
#     schema.add(colander.SchemaNode(
#         colander.Bool(),
#         name='subscribe_on_profile',
#         title=_("Show this list as a subscription option when a user registers or edits their profile?"),
#     ))
#
#
#
# def includeme(config):
#     config.add_subscriber(_subscriber_subscribe_on_profile, [FinishRegistrationSchema, ISchemaCreatedEvent])
#     config.add_subscriber(_subscriber_subscribe_on_profile, [UserSchema, ISchemaCreatedEvent])
#     config.add_subscriber(_list_option_for_profile, [EmailListSchema, ISchemaCreatedEvent])
