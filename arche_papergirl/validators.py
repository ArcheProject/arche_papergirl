import colander

from arche_papergirl import _


def multiple_email_validator(node, value):
    """
        checks that each line of value is a correct email
    """
    validator = colander.Email()
    invalid = []
    i=1
    for email in value.splitlines():
        try:
            validator(node, email)
        except colander.Invalid:
            invalid.append("%s (%s)" % (email, i))
        i+=1
    if invalid:
        emails = ", ".join(invalid)
        raise colander.Invalid(node, _(u"Invalid addresses found: ${emails}", mapping={'emails': emails}))
