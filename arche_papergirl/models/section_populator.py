from zope.interface import implementer

from arche_papergirl.interfaces import ISectionPopulatorUtil
from arche_papergirl.interfaces import INewsletterSection
from arche_papergirl import _


@implementer(ISectionPopulatorUtil)
class SectionPopulatorUtil(object):
    name = ''
    title = ''
    for_types = ()
    _renderer = None
    default_render_kw = {}

    def __init__(self, renderer,
                 schema_name = 'section_populator_ref',
                 name = '',
                 title = 'Unnamed populator',
                 for_types = ()):
        self._renderer = renderer
        self.schema_name = schema_name
        assert name
        self.name = name
        self.title = title
        self.for_types = for_types

    def render(self, context, request, **kw):
        render_kw = self.default_render_kw.copy()
        render_kw.update(kw)
        return self._renderer(context, request, **render_kw)

    def url(self, context, request):
        assert INewsletterSection.providedBy(context)
        return request.resource_url(context, 'populate', query = {'pop': self.name})

    def get_schema(self, context, request):
        bind = {'context': context, 'request': request, 'section_populator': self}
        return request.get_schema(context, 'NewsletterSection', self.schema_name, bind=bind, event=True)


def image_populator(context, request, alt='', width='100%', scale_name='col-12', from_uid = '', **kw):
    image = request.resolve_uid(from_uid)
    src = request.thumb_url(image, scale_name, key='file')
    return """<img src="{src}" alt="{alt}" width="{width}" />""".format(src= src, alt=alt, width=width)


def external_image_populator(context, request, src='', alt='', width='100%', url='', **kw):
    return """<img src="{src}" alt="{alt}" width="{width}" />""".format(src= url, alt=alt, width=width)


def add_section_populator(config, renderer,
                          schema_name = 'section_populator_ref',
                          name = '',
                          title = 'Unnamed populator',
                          for_types = (),):
    pop = SectionPopulatorUtil(renderer, schema_name=schema_name, name=name, title=title, for_types=for_types)
    config.registry.registerUtility(pop, name=pop.name)


def includeme(config):
    config.add_directive('add_section_populator', add_section_populator)
    config.add_section_populator(image_populator,
                                 name='image',
                                 title=_("Local image"),
                                 for_types=('Image',))
    config.add_section_populator(external_image_populator,
                                 name='external_image',
                                 title=_("External image"),
                                 schema_name='section_populator_external_url')
