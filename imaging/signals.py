from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .file_utils import delete_file_if_exists, get_previous_file
from .models import DatasetImage, UploadedImage


# If an existing row's `image` field is being replaced with a new file, delete the old file from storage once the new one is safely in place
# on `instance` (the new file is never touched — only the previous one).
@receiver(pre_save, sender=DatasetImage)
@receiver(pre_save, sender=UploadedImage)
def cleanup_old_image_on_replace(sender, instance, **kwargs):
    previous_file = get_previous_file(sender, instance.pk)
    if previous_file and previous_file.name and previous_file.name != instance.image.name:
        delete_file_if_exists(previous_file)


# Removes the associated file from storage whenever a row containing an
# uploaded image is deleted (including via Dataset cascade deletes).
@receiver(post_delete, sender=DatasetImage)
@receiver(post_delete, sender=UploadedImage)
def delete_image_file_on_row_delete(sender, instance, **kwargs):
    delete_file_if_exists(instance.image)