from pyramid.config import Configurator
from .middleware import AuthMiddleware

def main(global_config, **settings):

    config = Configurator(settings=settings)

    config.include("pyramid_jinja2")
    config.add_static_view(name="static", path="static")

    # Routes
    config.include('.routes')#Add Manually 
    config.include('.models')#Add Manually
    config.scan()

    app = config.make_wsgi_app()

    # Wrap Pyramid app with middleware
    app = AuthMiddleware(app)

    return app
