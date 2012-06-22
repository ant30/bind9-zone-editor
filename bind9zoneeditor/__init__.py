from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static/',
                           cache_max_age=86400)
    config.add_static_view('deform_static', 'deform:static')

    config.add_route('favicon', 'favicon.ico')
    config.add_route('record_delete', '{zonename}/{recordname}/delete')
    config.add_route('record_add', '{zonename}/add')
    config.add_route('apply', '{zonename}/applychanges')
    config.add_route('record', '{zonename}/{recordname}')
    config.add_route('zoneview', '{zonename}')
    config.add_route('zonelist', '')

    config.scan()

    return config.make_wsgi_app()
