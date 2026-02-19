def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    # Route for adding a model via the form in views.default.add_model
    config.add_route('add_model', '/add_model')
    config.add_route("signup", "/signup")
    config.add_route("login", "/login")
    config.add_route("dashboard", "/dashboard")
    config.add_route("logout", "/logout")
    
    # Product routes
    config.add_route('product_form', '/product_form')
    config.add_route('product_list', '/product_list')
    config.add_route('product_update', '/product/{id}/edit')
    config.add_route('product_delete', '/product/{id}/delete')
    config.add_route('product_soft_delete', '/product/{id}/soft_delete')
    config.add_route('profile', '/profile')
    config.add_route("refresh", "/refresh")

