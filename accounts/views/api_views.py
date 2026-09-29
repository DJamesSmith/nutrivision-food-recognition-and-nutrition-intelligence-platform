import json
import logging

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..decorators import jwt_required, log_execution_time
from ..serializers import LoginSerializer, RegisterSerializer, UserSerializer
from ..signals import login_failed, user_logged_in_custom, user_logged_out_custom, user_registered
from ..utils import TokenError, decode_refresh_token, generate_access_token, generate_refresh_token, \
    set_jwt_cookies, unset_jwt_cookies

logger = logging.getLogger(__name__)
User = get_user_model()


def _success(message, data=None, status=200):
    return JsonResponse({"status": "success", "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"status": "error", "message": message, "data": data}, status=status)


def _parse_json_body(request):
    try:
        return json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# POST /api/accounts/register/
@csrf_exempt
@require_http_methods(["POST"])
@log_execution_time
def register_api(request):
    payload = _parse_json_body(request)
    if payload is None:
        return _error("Malformed JSON body.", status=400)

    serializer = RegisterSerializer(data=payload)
    if not serializer.is_valid():
        return _error("Validation failed.", status=400, data=serializer.errors)

    user = serializer.save()
    user_registered.send(sender=register_api, user=user, request=request)
    logger.info("API registration: %s", user.email)

    return _success("Registration successful.", data=UserSerializer(user).data, status=201)


# POST /api/accounts/login/
@csrf_exempt
@require_http_methods(["POST"])
@log_execution_time
def login_api(request):
    payload = _parse_json_body(request)
    if payload is None:
        return _error("Malformed JSON body.", status=400)

    serializer = LoginSerializer(data=payload)
    if not serializer.is_valid():
        return _error("Validation failed.", status=400, data=serializer.errors)

    identifier = serializer.validated_data['identifier'].strip()
    password = serializer.validated_data['password']

    from django.contrib.auth import authenticate
    user = authenticate(request, identifier=identifier, password=password)

    if user is None:
        login_failed.send(sender=login_api, identifier=identifier, request=request)
        return _error("Authentication failed.", status=401)

    if not user.is_active:
        return _error("This account is inactive.", status=403)

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    user_logged_in_custom.send(sender=login_api, user=user, request=request)

    response = _success("Login successful.", data={"user": UserSerializer(user).data}, status=200)
    return set_jwt_cookies(response, access_token, refresh_token)


# POST /api/accounts/refresh/
@csrf_exempt
@require_http_methods(["POST"])
def refresh_api(request):
    refresh_token = request.COOKIES.get("refresh_token")

    try:
        payload = decode_refresh_token(refresh_token)
    except TokenError as exc:
        return _error(str(exc), status=401)

    try:
        user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        return _error("User for this token no longer exists.", status=401)

    if not user.is_active:
        return _error("This account is inactive.", status=403)

    new_access_token = generate_access_token(user)
    response = _success("Token refreshed.", data=None, status=200)
    return set_jwt_cookies(response, new_access_token)


# POST /api/accounts/logout/
@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def logout_api(request):
    user_logged_out_custom.send(sender=logout_api, user=request.user, request=request)
    response = _success("Logout successful.", data=None, status=200)
    return unset_jwt_cookies(response)


# GET /api/accounts/me/
@require_http_methods(["GET"])
@jwt_required
def me_api(request):
    return _success("Current user retrieved.", data=UserSerializer(request.user).data, status=200)
