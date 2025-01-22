from django.utils.timezone import now
from .models import VisitLog


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            VisitLog.objects.create(
                user=request.user,
                path=request.path,
                method=request.method,
                timestamp=now()
            )

        return response
