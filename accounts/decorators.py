import logging
import time
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .utils import TokenError, decode_access_token

logger = logging.getLogger(__name__)
User = get_user_model()


# Reusable JWT authentication decorator for function-based API views.
# - Reads the access token from the HTTP-only cookie (never from a header populated by JavaScript, since JS cannot read HttpOnly cookies).
# - Validates signature, algorithm and expiration.
# - Resolves the user and attaches it to request.user / request.auth_payload.
# - Returns a standardized 401 JSON error on any failure.
def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)

        try:
            payload = decode_access_token(token)
        except TokenError as exc:
            return JsonResponse({
                "status": "error",
                "message": str(exc),
                "data": None
            }, status=401)

        try:
            user = User.objects.get(pk=payload["user_id"])
        except (User.DoesNotExist, KeyError):
            return JsonResponse({
                "status": "error",
                "message": "User for this token no longer exists.",
                "data": None
            }, status=401)

        if not user.is_active:
            return JsonResponse({
                "status": "error",
                "message": "This account is inactive.",
                "data": None
            }, status=403)

        request.user = user
        request.auth_payload = payload
        return view_func(request, *args, **kwargs)
    return _wrapped


# Stack after @jwt_required. Rejects authenticated users who are not staff/admin — used for endpoints like initiating model training.
def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return JsonResponse({
                "status": "error",
                "message": "Authentication required.",
                "data": None
            }, status=401)
        if not (user.is_staff or user.is_superuser):
            return JsonResponse({
                "status": "error",
                "message": "Staff/admin privileges required.",
                "data": None
            }, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


# Reusable execution-time logging decorator. Wraps computationally expensive operations (model training, prediction, etc.) and logs how
# long they took. Preserves the wrapped function's metadata via @wraps.
def log_execution_time(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        start = time.perf_counter()
        try:
            return view_func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            logger.info(
                "EXECUTION_TIME | %s.%s completed in %.4fs",
                view_func.__module__, view_func.__qualname__, duration)
    return _wrapped
