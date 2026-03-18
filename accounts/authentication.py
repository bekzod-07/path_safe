from rest_framework.authentication import TokenAuthentication, get_authorization_header


class SwaggerTokenAuthentication(TokenAuthentication):
    keyword = "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if len(auth) == 1:
            token = auth[0].decode()
            return self.authenticate_credentials(token)

        if len(auth) == 2:
            prefix = auth[0].decode().lower()
            token = auth[1].decode()
            if prefix in ("token", "bearer"):
                return self.authenticate_credentials(token)

        return None