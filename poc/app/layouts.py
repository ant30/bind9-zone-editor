from pyramid.renderers import get_renderer
from pyramid.decorator import reify

class Layouts(object):

        @reify
        def global_template(self):
            renderer = get_renderer("templates/global_layout.pt")
            return renderer.implementation().macros['layout']

        @reify
        def global_macros(self):
            renderer = get_renderer("templates/macros.pt")
            return renderer.implementation().macros
