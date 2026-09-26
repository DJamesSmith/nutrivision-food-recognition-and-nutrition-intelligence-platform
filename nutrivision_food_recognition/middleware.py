# Adds Cache-Control: no-store (and Pragma: no-cache, for older/HTTP-1.0 caches) to every response under /api/ — prediction history, audit logs, training status, etc.
# Template pages already get the same treatment individually via @never_cache (see accounts/imaging/training/classification/audit views.py);
# this covers every REST endpoint in one place instead of decorating ~20 api_views.py functions by hand, and catches any future one that forgets to.


class NoCacheAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
        return response