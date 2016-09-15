import colander
import deform
from arche.widgets import ReferenceWidget
from arche_papergirl.validators import multiple_email_validator
from pyramid.renderers import render
from pyramid.traversal import find_interface

from arche_papergirl import _
from arche_papergirl.interfaces import IPostOffice
from arche_papergirl.utils import get_po_objs

@colander.deferred
def pick_email_template(node, kw):
    values = []
    context = kw['context']
    request = kw['request']
    for obj in get_po_objs(context, request, 'EmailListTemplate'):
        values.append((obj.uid, obj.title))
    return deform.widget.RadioChoiceWidget(values=values)


class NewsletterSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
        description = _("Used as first heading in the newsletter")
    )
    subject = colander.SchemaNode(
        colander.String(),
        title = _("Mail subject line"),
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _("Lead-in or description, included in the letter"),
        widget = deform.widget.TextAreaWidget(rows = 5),
        missing = "",
    )
    email_template = colander.SchemaNode(
        colander.String(),
        title = _("Pick a layout to use for this letter"),
        widget = pick_email_template,
        #validator = pick_list_validator
    )


class NewsletterSectionSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Section title"),
        missing = ""
    )
    body = colander.SchemaNode(
        colander.String(),
        title = _("Text"),
        widget = deform.widget.RichTextWidget(height = 300),
        missing = ""
    )
    # image_uid = colander.SchemaNode(colander.String(),
    #                            title = _("Image"),
    #                            widget = deform.widget.RichTextWidget(height = 300),
    #                            missing = "")
    # image_scale = colander.SchemaNode(colander.String(),
    #                            title = _("Text"),
    #                            widget = deform.widget.RichTextWidget(height = 300),
    #                            missing = "")

class AddNewsletterSectionSchema(colander.Schema):
    from_uid = colander.SchemaNode(
        colander.String(),
        title = _("Populate from this"),
        description = _("Leave it empty to create an empty section"),
        missing = "",
        widget = ReferenceWidget(multiple=False),
    )
    #Fetch image here and save scale + uid?


@colander.deferred
def current_users_email(node, kw):
    request = kw['request']
    return getattr(request.profile, 'email', '')

@colander.deferred
def pick_list_widget(node, kw):
    context = kw['context']
    request = kw['request']
    values = []
    for obj in get_po_objs(context, request, 'EmailList'):
        values.append((obj.uid, obj.title,))
    return deform.widget.RadioChoiceWidget(values=values)

@colander.deferred
def pick_lists_widget(node, kw):
    context = kw['context']
    request = kw['request']
    values = []
    for obj in get_po_objs(context, request, 'EmailList'):
        values.append((obj.uid, obj.title,))
    return deform.widget.CheckboxChoiceWidget(values=values)

#@colander.deferred
#def pick_list_validator(node, kw):
#    request = kw['request']
#   return colander.OneOf([x.uid for x in get_email_lists(request)])


class SendSingleRecipient(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        default = current_users_email,
        validator = colander.Email()
    )


class PreviewSchema(colander.Schema):
    description = _("preview_schema_description",
                    default="This will go to a blank page with an estimation of "
                            "how the newsletter will look. Remember "
                            "that mail clients may behave very different when they render email!")


class SendToLists(colander.Schema):
    recipient_list = colander.SchemaNode(
        colander.String(),
        title = _("Pick lists to send to"),
        widget = pick_list_widget,
        #validator = pick_list_validator
    )


@colander.deferred
def default_mail_template(node, kw):
    request = kw['request']
    values = {}
    return render('arche_papergirl:templates/default_mail_template.txt', values, request=request)


def mail_template_validator(node, kw):
    #FIXME
    pass


class EmailListSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("List title"),
    )


class EmailListTemplateSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Template title"),
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _("Description"),
        description = _("For internal use"),
        widget = deform.widget.TextAreaWidget(rows=2),
        missing = "",
    )
    body = colander.SchemaNode(
        colander.String(),
        title = _("Mail template"),
        #FIXME
        #description = _("mail_template_description",
        #                default="Variables should be entered as ${variable_name}. "
        #                        "The required variables are: "
        #                        "'title', 'body', 'unsubscribe_url' and 'list_title'. "
        #                       "You may also use html tags. "),
        widget = deform.widget.TextAreaWidget(rows=10),
        default = default_mail_template,
        missing = default_mail_template,
        validator = mail_template_validator,
    )


@colander.deferred
class UniqueSubscriberEmail(object):
    """ Make sure an email is unique. If it's used on a ListSubscriber object,
        it won't fail if the same address is used
    """
    def __init__(self, node, kw):
        self.context = kw['context']

    def __call__(self, node, value):
        email_val = colander.Email()
        email_val(node, value)
        post_office = find_interface(self.context, IPostOffice)
        #existing_mails = set([x for x in email_list.get_emails()])
        #if IListSubscriber.providedBy(self.context):
        #    existing_mails.remove(self.context.email)
        if value in post_office.subscribers.emails():
            raise colander.Invalid(node, _("already_used_email_error",
                                           default = "This address is already used."))


class ListSubscriberSchema(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        validator = UniqueSubscriberEmail,
    )


class RequestSubscriptionChangeSchema(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        validator = colander.Email()
    )


class PostOfficeSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title")
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _("Description"),
        widget = deform.widget.TextAreaWidget(rows = 5),
        missing = "",
    )


class UpdateListSubscribers(colander.Schema):
    emails = colander.SchemaNode(
        colander.String(),
        title=_("Email addresses, one per row."),
        widget=deform.widget.TextAreaWidget(rows=6),
        validator = multiple_email_validator,
    )
    lists = colander.SchemaNode(
        colander.Set(),
        title=_("Lists"),
        widget=pick_lists_widget,
    )


class EditListSubscriber(colander.Schema):
    list_references = colander.SchemaNode(
        colander.Set(),
        title=_("Lists"),
        widget=pick_lists_widget,
    )


@colander.deferred
def pick_unsubscribe_lists(node, kw):
    request = kw['request']
    context = kw['context']
    values = []
    for uid in context.list_references:
        obj = request.resolve_uid(uid)
        values.append((obj.uid, obj.title,))
    return deform.widget.CheckboxChoiceWidget(values=values)


class ManageUnsubscribeSchema(colander.Schema):
    lists = colander.SchemaNode(
        colander.Set(),
        title=_("Check any list to unsubscribe from it"),
        widget=pick_unsubscribe_lists,
    )


def includeme(config):
    config.add_content_schema('Newsletter', NewsletterSchema, ('add', 'edit'))
    config.add_content_schema('NewsletterSection', NewsletterSectionSchema, 'edit')
    config.add_content_schema('NewsletterSection', AddNewsletterSectionSchema, 'add')
    config.add_content_schema('Newsletter', SendSingleRecipient, 'send_single')
    config.add_content_schema('Newsletter', PreviewSchema, 'preview')
    config.add_content_schema('Newsletter', SendToLists, 'send_to_lists')
    config.add_content_schema('EmailList', EmailListSchema, ('add', 'edit'))
    config.add_content_schema('EmailListTemplate', EmailListTemplateSchema, ('add', 'edit', 'view'))
    config.add_content_schema('EmailList', RequestSubscriptionChangeSchema, 'request')
    config.add_content_schema('PostOffice', PostOfficeSchema, ('add', 'edit'))
    config.add_content_schema('ListSubscriber', UpdateListSubscribers, 'update')
    config.add_content_schema('ListSubscriber', EditListSubscriber, 'edit')
    config.add_content_schema('ListSubscriber', ManageUnsubscribeSchema, 'manage_unsubscribe')
