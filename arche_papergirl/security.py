from arche.security import ROLE_ADMIN
from arche.security import ROLE_VIEWER
from arche.security import ROLE_EDITOR
from arche.security import PERM_VIEW
from arche.security import PERM_EDIT
from arche.security import PERM_DELETE
from pyramid.security import ALL_PERMISSIONS

from arche_papergirl import _


PERM_ADD_NEWSLETTER = 'Add Newsletter'
PERM_ADD_EMAIL_LIST = 'Add Email list'
PERM_ADD_TEMPLATE = 'Add Email list template'
PERM_MANAGE_SUBSCRIBERS = 'Manage list subscribers'
PERM_VIEW_SUBSCRIBERS = 'View list subscribers'


def includeme(config):
    #config.register_roles(ROLE_NEWSLETTER_MANAGER, ROLE_NEWSLETTER_EDITOR)
    # ACL
    aclreg = config.registry.acl
    post_office_acl = aclreg.new_acl('PostOffice', title=_("Post Office"))
    post_office_acl.add(ROLE_ADMIN, ALL_PERMISSIONS)
    post_office_acl.add(ROLE_EDITOR, [PERM_VIEW, PERM_EDIT,
                                      PERM_ADD_NEWSLETTER,
                                      PERM_ADD_EMAIL_LIST,
                                      PERM_VIEW_SUBSCRIBERS,
                                      PERM_MANAGE_SUBSCRIBERS])
    post_office_acl.add(ROLE_VIEWER, [PERM_VIEW, PERM_VIEW_SUBSCRIBERS])
    #post_office_acl.add()
    #post_office_acl.add(ROLE_NEWSLETTER_MANAGER, _manager_perms)
    #post_office_acl.add(ROLE_NEWSLETTER_EDITOR, _nl_editor_perms)
