from wsgiref.simple_server import make_server

from pyramid.config import Configurator

def main():
    config = Configurator()

    config.add_static_view('static', 'static/',
                           cache_max_age=86400)
    config.add_static_view('deform_static', 'deform:static')

    config.add_route('favicon', 'favicon.ico')
    config.add_route('record', '{zonename}/{recordname}/{recordtype}')
    config.add_route('apply', '{zonename}/applychanges')
    config.add_route('zoneview', '{zonename}')
    config.add_route('zonelist', '')


    config.scan('views')

    app = config.make_wsgi_app()
    return app

if __name__ == '__main__':
    app = main()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
