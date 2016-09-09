
# @view_config(context=IListSubscribers,
#                permission=PERM_VIEW,
#                name='view',
#                renderer = 'arche:templates/form.pt')
# #FIXME: Check permission
# class ListSubscribersView(BaseForm):
#     schema_name = "search"
#     type_name = "ListSubscribers"
#     #title = _("Update subscribers")
#     formid = 'deform-search-subscribers'
#     #Important - make sure button names are unique since all forms will execute otherwise
#     buttons = (deform.Button('search', title = _("Search")),
#                deform.Button('cancel', title = _("Cancel")),)
#     use_ajax = True
#
#     ajax_options = """
#         {success:
#           function (rText, sText, xhr, form) {
#             console.log(rText);
#             //debugger;
#             arche.load_flash_messages();
#             /*
#             var loc = xhr.getResponseHeader('X-Relocate');
#             if (loc) {
#               document.location = loc;
#             };
#             */
#            }
#         }
#     """
#
#     def search_success(self, appstruct):
#         print appstruct
#         #self.flash_messages.add('blabla')
#         return _redirect_or_remove(self)
#
#     def cancel(self, *args):
#         return _redirect_or_remove(self)
#     cancel_success = cancel_failure = cancel


def includeme(config):
    config.scan(__name__)
