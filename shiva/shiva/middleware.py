from .security import verify_token

class AuthMiddleware:

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        path = environ.get("PATH_INFO", "")

        # Public routes
        public_routes = ["/login", "/signup", "/static"]

        if any(path.startswith(route) for route in public_routes):
            return self.app(environ, start_response)

        # Read cookies
        cookies = environ.get("HTTP_COOKIE", "")
        token = None

        for cookie in cookies.split(";"):
            if cookie.strip().startswith("token="):
                token = cookie.strip().split("=")[1]

        if token:
            user_data = verify_token(token)
            if user_data:
                environ["user"] = user_data
                return self.app(environ, start_response)

        # Redirect to login
        start_response("302 Found", [("Location", "/login")])
        return [b"Redirecting to login..."]
