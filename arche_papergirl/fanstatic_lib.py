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



#def include_resources(view, event):


def includeme(config):
    pass
    #config.add_subscriber(include_resources, [IBaseView, IViewInitializedEvent])