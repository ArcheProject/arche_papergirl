import colander
import deform
from arche.widgets import ReferenceWidget

from arche_papergirl import _


class NewsletterSchema(colander.Schema):
    title = colander.SchemaNode(colander.String(),
                                title = _("Title"))


class NewsletterSectionSchema(colander.Schema):
    title = colander.SchemaNode(colander.String(),
                                title = _("Title"),
                                missing = "")
    body = colander.SchemaNode(colander.String(),
                               title = _("Text"),
                               widget = deform.widget.RichTextWidget(height = 300),
                               missing = "")
    # image_uid = colander.SchemaNode(colander.String(),
    #                            title = _("Image"),
    #                            widget = deform.widget.RichTextWidget(height = 300),
    #                            missing = "")
    # image_scale = colander.SchemaNode(colander.String(),
    #                            title = _("Text"),
    #                            widget = deform.widget.RichTextWidget(height = 300),
    #                            missing = "")

class AddNewsletterSectionSchema(colander.Schema):
    from_uid = colander.SchemaNode(colander.String(),
                                   title = _("Populate from this"),
                                   description = _("Leave it empty to create an empty section"),
                                   missing = "",
                                   widget = ReferenceWidget(multiple=False),)
    #Fetch image here and save scale + uid?


@colander.deferred
def current_users_email(node, kw):
    request = kw['request']
    return getattr(request.profile, 'email', '')


class SendSingleRecipient(colander.Schema):
    email = colander.SchemaNode(colander.String(),
                                title = _("Email"),
                                default = current_users_email,
                                validator = colander.Email())

def _get_lists(context, request):
    #FIXME
    return [('hello', 'Hello')]

@colander.deferred
def pick_lists_widget(node, kw):
    context = kw['context']
    request = kw['request']
    return deform.widget.CheckboxChoiceWidget(values = _get_lists(context, request))

@colander.deferred
def pick_lists_validator(node, kw):
    context = kw['context']
    request = kw['request']
    values = [x[0] for x in _get_lists(context, request)]
    return colander.ContainsOnly(values)


class SendToList(colander.Schema):
    recipient_lists = colander.SchemaNode(colander.Set(),
                                          title = _("Pick lists to send to"),
                                          widget = pick_lists_widget,
                                          validator = pick_lists_validator)


def includeme(config):
    config.add_content_schema('Newsletter', NewsletterSchema, ('add', 'edit'))
    config.add_content_schema('NewsletterSection', NewsletterSectionSchema, 'edit')
    config.add_content_schema('NewsletterSection', AddNewsletterSectionSchema, 'add')
    config.add_content_schema('Newsletter', SendSingleRecipient, 'send_single')
    config.add_content_schema('Newsletter', SendToList, 'send_to_list')
