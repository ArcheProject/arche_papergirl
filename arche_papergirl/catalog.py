from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from arche_papergirl.interfaces import IListSubscriber


def _get_subscribed_lists(context, default):
    if IListSubscriber.providedBy(context):
        return tuple(context.list_references)
    return default


def includeme(config):
    indexes = {
        'subscribed_lists': CatalogKeywordIndex(_get_subscribed_lists),
    }
    config.add_catalog_indexes(__name__, indexes)
