from arche.fanstatic_lib import common_js
from arche.fanstatic_lib import main_css
from arche.fanstatic_lib import pure_js
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from deform_autoneed import resource_registry
from fanstatic import Library
from fanstatic import Resource
from js.bootstrap import bootstrap_css
from js.jquery import jquery


papergirl_lib = Library('papergirl', 'static')

paper_manage = Resource(papergirl_lib, 'manage.js', depends=(common_js, pure_js))
ace_js = Resource(papergirl_lib, 'ace-noconflict/ace.js', minified='ace-min-noconflict/ace.js')

#def include_resources(view, event):


def includeme(config):
    pass
    #config.add_subscriber(include_resources, [IBaseView, IViewInitializedEvent])
