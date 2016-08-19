from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('arche_papergirl')


def includeme(config):
    config.include('.models')
    config.include('.schemas')
    config.include('.views')

def subscribe_on_profile(config):
    """ Include this to allow users to subscribe to marked lists in their profiles.
    """
    config.include('.schemas.subscribe_on_profile')
    config.include('.models.subscribe_on_profile')
