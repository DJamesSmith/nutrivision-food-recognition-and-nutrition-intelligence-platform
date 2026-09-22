from django.conf import settings
from django.db import models
from imaging.models import Dataset


class TrainingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        STARTED = 'STARTED', 'Started'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    # PROTECT: a dataset that has ever been used for training should not be silently deletable out from under its training history.
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT, related_name='training_jobs')                                        # ForeignKey

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    task_id = models.CharField(max_length=255, blank=True, db_index=True)

    epochs = models.PositiveIntegerField(default=10)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    accuracy = models.FloatField(null=True, blank=True)
    validation_accuracy = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    validation_loss = models.FloatField(null=True, blank=True)

    model_path = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='training_jobs')        # ForeignKey
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_job'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', '-created_at'])]

    def __str__(self):
        return f"TrainingJob #{self.id} [{self.status}] — {self.dataset.name}"

    def is_terminal(self):
        return self.status in (self.Status.COMPLETED, self.Status.FAILED)


class ModelVersion(models.Model):
    version = models.CharField(max_length=32, unique=True)
    architecture = models.CharField(max_length=100, default='EfficientNetB0')
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT, related_name='model_versions')                                       # ForeignKey
    training_job = models.OneToOneField(TrainingJob, on_delete=models.SET_NULL, null=True, blank=True, related_name='model_version')

    # Ordered list of class names; index position == the model's output neuron index. This is what makes the number of classes fully
    # dynamic — nothing about class count is hard-coded anywhere.
    class_labels = models.JSONField(default=list)
    num_classes = models.PositiveIntegerField()

    accuracy = models.FloatField(null=True, blank=True)
    validation_accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)

    model_path = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_model_version'
        ordering = ['-created_at']

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.version} ({self.architecture}, {status})"