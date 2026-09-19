import os

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp'])
MAX_IMAGE_UPLOAD_SIZE_MB = getattr(settings, 'MAX_IMAGE_UPLOAD_SIZE_MB', 10)

# Pillow's reported format for each allowed extension, used as a loose
# MIME/content sanity check (Pillow does not give us the browser's MIME
# type, so we check its own parsed format instead).
_EXTENSION_TO_PIL_FORMAT = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
}


def validate_image_file(uploaded_file):
    """
    Validates an uploaded image file for extension, size, and integrity.
    Raises django.core.exceptions.ValidationError on any failure.
    Used by both Django forms (session uploads) and DRF serializers
    (API uploads) so the rules live in exactly one place.
    """
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
        )

    max_bytes = MAX_IMAGE_UPLOAD_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"Image exceeds the maximum allowed size of {MAX_IMAGE_UPLOAD_SIZE_MB} MB.")

    # Verify the file is a genuine, uncorrupted image and that its real
    # format roughly matches its extension.
    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as img:
            img.verify()
            detected_format = img.format
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("The uploaded file is not a valid or is a corrupted image.")
    finally:
        uploaded_file.seek(0)

    expected_format = _EXTENSION_TO_PIL_FORMAT.get(ext)
    if expected_format and detected_format != expected_format:
        raise ValidationError(
            f"File content does not match its extension (expected {expected_format}, got {detected_format})."
        )
