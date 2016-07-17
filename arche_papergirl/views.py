import deform
from arche.security import PERM_EDIT
from arche.security import NO_PERMISSION_REQUIRED
from arche.utils import get_content_schemas
from arche.views.base import BaseView, DefaultAddForm, BaseForm
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults

from arche_papergirl import _
from arche_papergirl.interfaces import INewsletter, INewsletterSection


@view_defaults(context = INewsletter, permission = PERM_EDIT)
class NewsletterView(BaseView):

    @view_config(name = 'view', renderer = 'arche_papergirl:templates/newsletter.pt')
    def view(self):
        sections = [x for x in self.context.values() if INewsletterSection.providedBy(x)]
        single_form = SendSingleSubForm(self.context, self.request)()
        to_list_form = SendToListSubForm(self.context, self.request)()
        for subform in (single_form, to_list_form):
            if isinstance(subform, Exception):
                if isinstance(subform, HTTPFound):
                    return subform
                raise subform
        return {'sections': sections,
                'send_single_form': single_form['form'],
                'send_to_list_form': to_list_form['form']}


class SendSingleSubForm(BaseForm):
    schema_name = "send_single"
    type_name = "Newsletter"
    title = _("Send to single recipient")
    formid = 'deform-send-single'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_single', title = _("Send")),)
    #use_ajax = True

    @property
    def form_options(self):
        options = super(SendSingleSubForm, self).form_options
        options['action'] = self.request.resource_url(self.context, anchor='test_tab')
        return options
        # return {'action': self.request.url,
        #         'heading': self.get_schema_heading(),
        #         'tab_fields': self._tab_fields,
        #         'tab_titles': self.tab_titles,
        #         'formid': self.formid,
        #         'request': self.request}

    def send_single_success(self, appstruct):
        #???
        self.flash_messages.add(self.default_success, type='success')
        print appstruct
        return HTTPFound(location=self.request.resource_url(self.context))

class SendToListSubForm(BaseForm):
    schema_name = "send_to_list"
    type_name = "Newsletter"
    title = _("Send to list")
    formid = 'deform-to-list'
    #Important - make sure button names are unique since all forms will execute otherwise
    buttons = (deform.Button('send_to_list', title = _("Send")),)
    #use_ajax = True

    def send_to_list_success(self, appstruct):
        self.flash_messages.add(self.default_success, type='success')
        print appstruct
        return HTTPFound(location=self.request.resource_url(self.context))

@view_config(context = INewsletter,
             name = 'add',
             permission = NO_PERMISSION_REQUIRED,
             renderer = 'arche:templates/form.pt')
class AddSectionForm(DefaultAddForm):

    def save_success(self, appstruct):
        #populate from referenced, or create blank
        section_appstruct = {}
        return super(AddSectionForm, self).save_success(section_appstruct)
        #self.flash_messages.add(self.default_success, type="success")
        #factory = self.get_content_factory(self.type_name)
        #obj = factory(**appstruct)
        #naming_attr = getattr(obj, 'naming_attr', 'title')
        #name = generate_slug(self.context, getattr(obj, naming_attr, ''))
        #self.context[name] = obj
        #return HTTPFound(location = self.request.resource_url(obj))


@view_config(context=INewsletterSection,
             permission = NO_PERMISSION_REQUIRED)
def redirect_to_parent_uid_anchor(context, request):
    url = request.resource_url(context.__parent__, anchor = context.uid)
    return HTTPFound(location = url)


def includeme(config):
    config.scan(__name__)
