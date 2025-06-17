# backend/common/middleware.py
from django.http import HttpResponsePermanentRedirect

class DisableHttpsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.is_secure():
            return HttpResponsePermanentRedirect(request.build_absolute_uri().replace("https://", "http://"))
        return self.get_response(request)
