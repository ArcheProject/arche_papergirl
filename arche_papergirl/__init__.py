
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('arche_papergirl')

base_config_values = {'papergirl.mail_css': 'arche_papergirl:static/mail_base.css',
                      'papergirl.use_celery': None}


def includeme(config):
    config.include('.catalog')
    config.include('.subscribers')
    config.include('.models')
    config.include('.schemas')
    config.include('.portlets')
    config.include('.security')
    config.include('.views')
    config.add_translation_dirs('arche_papergirl:locale/')

    settings = config.registry.settings
    #Populate with default settings
    for (k, v) in base_config_values.items():
        if k not in settings:
            settings[k] = v
    check_and_convert_css(config)

    #Check if celery is configured and available
    #FIXME: Might be good to drop this
    use_celery = settings.get('papergirl.use_celery', None)
    if use_celery is None:
        try:
            import arche_celery
            settings['papergirl.use_celery'] = True
        except ImportError:
            settings['papergirl.use_celery'] = False


def check_and_convert_css(config):
    from os.path import isfile
    from pyramid.path import AssetResolver
    settings = config.registry.settings
    resolver = AssetResolver()
    assets = []
    for relpath in settings.get('papergirl.mail_css', '').splitlines():
        if not relpath:
            continue
        resolved = resolver.resolve(relpath)
        abspath = resolved.abspath()
        if isfile(abspath):
            assets.append(relpath)
        else:
            raise IOError("papergirl.mail_css setting points to nonexistent file: %s" % abspath)
    settings['papergirl.mail_css'] = assets
