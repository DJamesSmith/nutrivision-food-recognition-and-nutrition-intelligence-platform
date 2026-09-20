from django.conf import settings
from django.db import models

from imaging.models import UploadedImage
from training.models import ModelVersion


class Prediction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='predictions')

    # SET_NULL: a prediction's historical record (class, confidence, model version, timestamp) must survive even if the source image is later
    # cleaned up from storage.
    uploaded_image = models.ForeignKey(
        UploadedImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predictions')

    # PROTECT: a ModelVersion that has real predictions attached to it
    # should not be deletable — it's now part of the audit trail.
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.PROTECT,
        related_name='predictions')

    predicted_class = models.CharField(max_length=150)
    confidence = models.FloatField()

    # Full probability distribution across every class the active model knows about, e.g. {"pizza": 0.94, "salad": 0.06} — kept for
    # transparency/debugging, not just the single winning class.
    class_probabilities = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classification_prediction'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"{self.predicted_class} ({self.confidence:.2%}) — {self.user}"
