import datetime
import uuid
import jwt
from django.conf import settings


# Raised for any invalid/expired/malformed JWT.
class TokenError(Exception):
    pass


def _base_payload(user, token_type, lifetime):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return {
        "user_id": str(user.pk),
        "email": user.email,
        "token_type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + lifetime,
    }


def generate_access_token(user):
    payload: dict = _base_payload(
        user, "access",
        datetime.timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES))
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token(user):
    payload: dict = _base_payload(
        user, "refresh",
        datetime.timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS))
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token):
    return _decode(token, settings.JWT_SECRET_KEY, expected_type="access")


def decode_refresh_token(token):
    return _decode(token, settings.JWT_REFRESH_SECRET_KEY, expected_type="refresh")


def _decode(token, secret, expected_type):
    if not token:
        raise TokenError("No token provided.")
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired.")
    except jwt.InvalidAlgorithmError:
        raise TokenError("Token uses an unsupported signing algorithm.")
    except jwt.InvalidTokenError:
        raise TokenError("Token is invalid.")

    if payload.get("token_type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token.")

    return payload


def set_jwt_cookies(response, access_token, refresh_token=None):
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access_token,
        max_age=settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        httponly=settings.JWT_COOKIE_HTTPONLY,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path='/',
    )
    if refresh_token is not None:
        response.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            refresh_token,
            max_age=settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            path='/',
        )
    return response


def unset_jwt_cookies(response):
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path='/')
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path='/')
    return response