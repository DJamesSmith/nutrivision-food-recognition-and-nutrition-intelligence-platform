import uuid
from django.conf import settings
from django.db import models
from .validators import validate_image_file


def dataset_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f"datasets/{instance.dataset_id}/{instance.class_label}/{uuid.uuid4().hex}.{ext}"


def uploaded_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f"uploaded_images/{instance.user_id}/{uuid.uuid4().hex}.{ext}"


class Dataset(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        READY = 'READY', 'Ready for Training'
        ARCHIVED = 'ARCHIVED', 'Archived'

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_datasets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'imaging_dataset'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_num_classes(self):
        return self.images.values('class_label').distinct().count()

    def get_class_distribution(self):
        return (
            self.images.values('class_label')
            .annotate(count=models.Count('id'))
            .order_by('class_label'))

    def get_num_images(self):
        return self.images.count()


class DatasetImage(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=dataset_image_upload_path, validators=[validate_image_file])
    class_label = models.CharField(max_length=100, db_index=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_dataset_images',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imaging_dataset_image'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['dataset', 'class_label'])]

    def __str__(self):
        return f"{self.dataset.name} / {self.class_label} / {self.image.name}"


# General-purpose uploaded image, independent of any training dataset.
# Used for on-demand uploads such as prediction requests: the classification app (Phase 5) references this model rather than
# duplicating upload/validation/cleanup logic.
class UploadedImage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_images',
    )
    image = models.ImageField(upload_to=uploaded_image_upload_path, validators=[validate_image_file])
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imaging_uploaded_image'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user_id} / {self.image.name}"
