from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework import exceptions


class SwaggerTokenAuthentication(TokenAuthentication):
    """
    Swagger uchun qulay auth:
    1) Token abc123
    2) Bearer abc123
    3) abc123
    uchalasini ham qabul qiladi.
    """

    keyword = "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        try:
            # Faqat token yuborilgan bo‘lsa:
            # Authorization: abc123
            if len(auth) == 1:
                token = auth[0].decode("utf-8")
                return self.authenticate_credentials(token)

            # Prefix bilan yuborilgan bo‘lsa:
            # Authorization: Token abc123
            # Authorization: Bearer abc123
            if len(auth) == 2:
                prefix = auth[0].decode("utf-8").lower()
                token = auth[1].decode("utf-8")

                if prefix in ("token", "bearer"):
                    return self.authenticate_credentials(token)

            raise exceptions.AuthenticationFailed("Noto‘g‘ri Authorization header formati")
        except UnicodeError:
            raise exceptions.AuthenticationFailed("Token header noto‘g‘ri")