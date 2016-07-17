from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('arche_papergirl')


def includeme(config):
    config.include('.models')
    config.include('.schemas')
    config.include('.views')
