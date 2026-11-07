"""Cabeçalhos de segurança (CSP). O frontend não usa scripts/estilos inline, então a política
pode ser restritiva. O Django Admin (/django-admin/) fica fora da política por usar inline."""


class SecurityHeadersMiddleware:
    CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
           "connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith("/django-admin/"):
            response.setdefault("Content-Security-Policy", self.CSP)
        response.setdefault("Referrer-Policy", "same-origin")
        return response
