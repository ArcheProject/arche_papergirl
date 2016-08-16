import colander
import deform
from arche.widgets import ReferenceWidget

from arche_papergirl import _
from pyramid.renderers import render


class NewsletterSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title")
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _("Lead-in or description, included in the letter"),
        widget = deform.widget.TextAreaWidget(rows = 5),
    )


class NewsletterSectionSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
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

def _get_lists(context, request):
    #FIXME
    values = [('', _("<Select>"))]
    query = "type_name == 'EmailList'"
    docids = request.root.catalog.query(query)[1]
    for obj in request.resolve_docids(docids):
        title = "%s (%s)" % (obj.title, len(obj))
        values.append((obj.uid, title))
    return values

@colander.deferred
def pick_list_widget(node, kw):
    context = kw['context']
    request = kw['request']
    return deform.widget.RadioChoiceWidget(values = _get_lists(context, request))

@colander.deferred
def pick_list_validator(node, kw):
    context = kw['context']
    request = kw['request']
    values = [x[0] for x in _get_lists(context, request)]
    return colander.OneOf(values)

class SendSingleRecipient(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        default = current_users_email,
        validator = colander.Email()
    )
    recipient_list = colander.SchemaNode(
        colander.String(),
        title = _("Pick list layout to use"),
        widget = pick_list_widget,
        validator = pick_list_validator
    )

class SendToList(colander.Schema):
    recipient_list = colander.SchemaNode(
        colander.String(),
        title = _("Pick list to send to"),
        widget = pick_list_widget,
        validator = pick_list_validator
    )


@colander.deferred
def default_mail_template(node, kw):
    request = kw['request']
    #context = kw['context']
    values = {}
    return render('arche_papergirl:templates/default_mail_template.txt', values, request=request)

def mail_template_validator(node, kw):
    pass
#FIXME

class EmailListSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("List title"),
    )
    mail_template = colander.SchemaNode(
        colander.String(),
        title = _("Mail template"),
        description = _("mail_template_description",
                        default="Variables should be entered as {{variable_name}}. "
                                "The required variables are: "
                                "'title', 'body', 'unsubscribe_url' and 'list_title'. "
                                "You may also use html tags. "),
        widget = deform.widget.TextAreaWidget(rows=10),
        default = default_mail_template,
        missing = default_mail_template,
        validator = mail_template_validator,
    )


class ListSubscriberSchema(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        validator = colander.Email()
    ) #FIXME: Unique email
    active = colander.SchemaNode(
        colander.Bool(),
        title = _("Active subscription?")
    )


class RequestSubscriptionChangeSchema(colander.Schema):
    email = colander.SchemaNode(
        colander.String(),
        title = _("Email"),
        validator = colander.Email()
    )


def includeme(config):
    config.add_content_schema('Newsletter', NewsletterSchema, ('add', 'edit'))
    config.add_content_schema('NewsletterSection', NewsletterSectionSchema, 'edit')
    config.add_content_schema('NewsletterSection', AddNewsletterSectionSchema, 'add')
    config.add_content_schema('Newsletter', SendSingleRecipient, 'send_single')
    config.add_content_schema('Newsletter', SendToList, 'send_to_list')
    config.add_content_schema('EmailList', EmailListSchema, ('add', 'edit'))
    config.add_content_schema('ListSubscriber', ListSubscriberSchema, ('add', 'edit', 'view'))
    config.add_content_schema('EmailList', RequestSubscriptionChangeSchema, 'request')
