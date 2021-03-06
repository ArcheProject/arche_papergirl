from arche.security import ROLE_ADMIN
from arche.security import ROLE_VIEWER
from arche.security import ROLE_EDITOR
from arche.security import PERM_VIEW
from arche.security import PERM_EDIT
from pyramid.security import ALL_PERMISSIONS

from arche_papergirl import _


PERM_ADD_EMAIL_LIST = 'Add Email list'
PERM_ADD_TEMPLATE = 'Add Email list template'
PERM_ADD_NEWSLETTER = 'Add Newsletter'
PERM_ADD_NEWSLETTER_SECTION = 'Add Newsletter section'
PERM_ADD_POST_OFFICE = 'Add Post office'
PERM_MANAGE_SUBSCRIBERS = 'Manage list subscribers'
PERM_VIEW_SUBSCRIBERS = 'View list subscribers'


def includeme(config):
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
