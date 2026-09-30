import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required, staff_required
from audit.models import AuditLog
from audit.services import log_event
from imaging.models import Dataset

from ..ml_pipeline import DatasetValidationError, validate_dataset_for_training
from ..models import ModelVersion, TrainingJob
from ..serializers import ModelVersionSerializer, TrainingJobSerializer
from ..services import activate_model_version
from ..tasks import train_model_task

logger = logging.getLogger(__name__)


def _success(message, data=None, status=200):
    return JsonResponse({"status": "success", "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"status": "error", "message": message, "data": data}, status=status)


# POST /api/training/train/
@require_http_methods(["POST"])
@jwt_required
@staff_required
def train_api(request):
    try:
        payload = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Malformed JSON body.", status=400)

    dataset_id = payload.get('dataset_id')
    if not dataset_id:
        return _error("dataset_id is required.", status=400)

    dataset = get_object_or_404(Dataset, pk=dataset_id)

    try:
        validate_dataset_for_training(dataset)
    except DatasetValidationError as exc:
        return _error(str(exc), status=409)

    epochs = payload.get('epochs')
    if epochs is not None:
        try:
            epochs = int(epochs)
            if epochs <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return _error("epochs must be a positive integer.", status=400)

    job = TrainingJob.objects.create(
        dataset=dataset,
        epochs=epochs or settings.DEFAULT_TRAINING_EPOCHS_HEAD,
        created_by=request.user)

    # Training must NOT execute inside this request — queue it and return immediately with the task id.
    async_result = train_model_task.delay(job.id)
    job.task_id = async_result.id
    job.save(update_fields=['task_id'])

    log_event(
        AuditLog.EventType.TRAINING_STARTED, user=request.user, request=request,
        description=f"Training queued for dataset '{dataset.name}' (job #{job.id}).",
        reference_model='TrainingJob', reference_id=job.id)

    return _success(
        "Model training has been queued.",
        data={"task_id": async_result.id, "training_job_id": job.id},
        status=202)


# GET /api/training/jobs/
@require_http_methods(["GET"])
@jwt_required
@staff_required
def training_job_list_api(request):
    jobs = TrainingJob.objects.select_related('dataset').all()[:100]
    return _success("Training jobs retrieved.", data=TrainingJobSerializer(jobs, many=True).data)


# GET /api/training/jobs/<id>/
@require_http_methods(["GET"])
@jwt_required
@staff_required
def training_job_detail_api(request, job_id):
    job = get_object_or_404(TrainingJob, pk=job_id)
    return _success("Training job retrieved.", data=TrainingJobSerializer(job).data)


# GET /api/training/models/
@require_http_methods(["GET"])
@jwt_required
@staff_required
def model_version_list_api(request):
    versions = ModelVersion.objects.select_related('dataset').all()[:100]
    return _success("Model versions retrieved.", data=ModelVersionSerializer(versions, many=True).data)


# POST /api/training/models/<id>/activate/
@require_http_methods(["POST"])
@jwt_required
@staff_required
def model_version_activate_api(request, version_id):
    version = get_object_or_404(ModelVersion, pk=version_id)
    activate_model_version(version)

    log_event(
        AuditLog.EventType.MODEL_UPDATED, user=request.user, request=request,
        description=f"Model version {version.version} manually activated.",
        reference_model='ModelVersion', reference_id=version.id)

    return _success("Model version activated.", data=ModelVersionSerializer(version).data)
