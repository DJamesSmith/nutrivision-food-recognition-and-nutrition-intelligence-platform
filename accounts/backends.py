import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

PHONE_RE = re.compile(r'^\+?[1-9]\d{7,14}$')


# Authenticates a user against either their email address or their phone number, using a single 'identifier' credential.
# Works transparently with Django's session-authentication framework (login()/logout()).
class EmailOrPhoneBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        login_id = identifier or username
        if login_id is None or password is None:
            return None

        login_id = login_id.strip()

        try:
            if PHONE_RE.match(login_id):
                user = User.objects.get(phone_number=login_id)
            else:
                user = User.objects.get(Q(email__iexact=login_id))
        except User.DoesNotExist:
            # Run the hasher anyway to keep response timing consistent and avoid leaking whether the identifier exists.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
