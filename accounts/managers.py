from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError


# Manager for the custom User model. Users are identified primarily by email; phone number is a required, unique, secondary identifier that
# can also be used to log in (see accounts.backends.EmailOrPhoneBackend).
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, phone_number, password, **extra_fields):
        if not email:
            raise ValueError("The Email field is required.")
        if not phone_number:
            raise ValueError("The Phone number field is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)
        return user

    def create_user(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, phone_number, password, **extra_fields)

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('is_phone_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValidationError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError("Superuser must have is_superuser=True.")

        return self._create_user(email, phone_number, password, **extra_fields)
