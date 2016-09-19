from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('arche_papergirl')


def includeme(config):
    config.include('.catalog')
    config.include('.subscribers')
    config.include('.models')
    config.include('.schemas')
    config.include('.security')
    config.include('.views')
