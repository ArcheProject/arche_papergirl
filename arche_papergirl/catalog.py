from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from arche_papergirl.interfaces import IListSubscriber


def _get_list_references(context, default):
    if IListSubscriber.providedBy(context):
        return tuple(context.list_references)
    return default

#FIXME: Write catalog tests to properly check reindexing when using update

def includeme(config):
    indexes = {
        'list_references': CatalogKeywordIndex(_get_list_references),
    }
    config.add_catalog_indexes(__name__, indexes)
