from .security import verify_token, create_access_token
from jwt import ExpiredSignatureError, InvalidTokenError


class AuthMiddleware:

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        path = environ.get("PATH_INFO", "")

        public_routes = ["/login", "/signup", "/refresh", "/static"]

        if any(path.startswith(route) for route in public_routes):
            return self.app(environ, start_response)

        cookies = environ.get("HTTP_COOKIE", "")
        token = None

        for cookie in cookies.split(";"):
            if cookie.strip().startswith("token="):
                token = cookie.strip().split("=")[1]

        if token:
            try:
                payload = verify_token(token)

                # ✅ CREATE NEW ACCESS TOKEN EVERY REQUEST
                new_access_token = create_access_token({
                    "user_id": payload["user_id"]
                })

                def custom_start_response(status, headers, exc_info=None):
                    headers.append((
                        "Set-Cookie",
                        f"token={new_access_token}; "
                        f"HttpOnly; Path=/; SameSite=Strict; Max-Age=600"
                    ))
                    return start_response(status, headers, exc_info)

                environ["user"] = payload

                return self.app(environ, custom_start_response)

            except ExpiredSignatureError:
                start_response("302 Found", [("Location", "/refresh")])
                return [b"Access expired"]

            except InvalidTokenError:
                pass

        start_response("302 Found", [("Location", "/login")])
        return [b"Redirecting to login"]