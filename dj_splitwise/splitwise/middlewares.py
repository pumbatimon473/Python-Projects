from django.http import HttpRequest, HttpResponse
import json
import http


class ExceptionMiddleware:
    def __init__(self, forward_request):
        """

        :param forward_request: A callable that forwards the request to the next middleware (if any) or the view
        """
        self.get_response = forward_request

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse:
        """Any unattended exception raised by the view will be caught here"""
        return HttpResponse(
            json.dumps({
                'error': str(exception),
                'meta': 'Caught by Middleware Hook'
            }),
            status=http.HTTPStatus.BAD_REQUEST,
            content_type='application/json',
            charset='utf-8'
        )
