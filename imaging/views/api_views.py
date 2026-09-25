import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from accounts.decorators import jwt_required, log_execution_time, staff_required
from audit.models import AuditLog
from audit.services import log_event

from ..models import Dataset, DatasetImage, UploadedImage
from ..serializers import DatasetImageSerializer, DatasetSerializer, UploadedImageSerializer

logger = logging.getLogger(__name__)


def _success(message, data=None, status=200):
    return JsonResponse({"status": "success", "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"status": "error", "message": message, "data": data}, status=status)


# GET/POST /api/imaging/datasets/
@require_http_methods(["GET", "POST"])
@jwt_required
@staff_required
def dataset_list_create_api(request):
    if request.method == 'GET':
        datasets = Dataset.objects.all()
        return _success(
            "Datasets retrieved.",
            data=DatasetSerializer(datasets, many=True).data)

    # POST — dataset creation is metadata-only (JSON), not a file upload.
    import json
    try:
        payload = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Malformed JSON body.", status=400)

    serializer = DatasetSerializer(data=payload)
    if not serializer.is_valid():
        return _error("Validation failed.", status=400, data=serializer.errors)

    dataset = Dataset.objects.create(
        name=serializer.validated_data['name'],
        description=serializer.validated_data.get('description', ''),
        created_by=request.user)
    return _success("Dataset created.", data=DatasetSerializer(dataset).data, status=201)


# GET /api/imaging/datasets/<id>/
@require_http_methods(["GET"])
@jwt_required
@staff_required
def dataset_detail_api(request, dataset_id):
    dataset = get_object_or_404(Dataset, pk=dataset_id)
    data = DatasetSerializer(dataset).data
    data['class_distribution'] = list(dataset.get_class_distribution())
    return _success("Dataset retrieved.", data=data)


# POST /api/imaging/datasets/<id>/images/
@require_http_methods(["POST"])
@jwt_required
@staff_required
@log_execution_time
def dataset_image_upload_api(request, dataset_id):
    dataset = get_object_or_404(Dataset, pk=dataset_id)

    image_file = request.FILES.get('image')
    class_label = (request.POST.get('class_label') or '').strip()

    if not image_file:
        return _error("No image file was provided.", status=400)
    if not class_label:
        return _error("A class_label is required.", status=400)

    instance = DatasetImage(dataset=dataset, class_label=class_label, uploaded_by=request.user)
    instance.image = image_file

    try:
        instance.full_clean()
    except Exception as exc:
        message = "; ".join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        return _error(f"Validation failed: {message}", status=400)

    instance.save()

    log_event(
        AuditLog.EventType.IMAGE_UPLOADED,
        user=request.user,
        request=request,
        description=f"Dataset image uploaded to '{dataset.name}' (class: {class_label}).",
        reference_model='DatasetImage',
        reference_id=instance.id)

    return _success("Image uploaded successfully.", data=DatasetImageSerializer(instance).data, status=201)


# DELETE /api/imaging/datasets/<id>/images/<image_id>/
@require_http_methods(["DELETE"])
@jwt_required
@staff_required
def dataset_image_delete_api(request, dataset_id, image_id):
    image = get_object_or_404(DatasetImage, pk=image_id, dataset_id=dataset_id)
    image.delete()  # triggers imaging.signals post_delete file cleanup
    return _success("Image deleted.", data=None)


# General-purpose image upload for any authenticated user (not just staff) — e.g. the image a user wants classified.
# The classification app will accept an UploadedImage id in its predict endpoint.
# POST /api/imaging/images/upload/
@require_http_methods(["POST"])
@jwt_required
@log_execution_time
def uploaded_image_create_api(request):
    image_file = request.FILES.get('image')
    if not image_file:
        return _error("No image file was provided.", status=400)

    instance = UploadedImage(
        user=request.user,
        original_filename=image_file.name,
        content_type=getattr(image_file, 'content_type', '') or '',
        file_size=image_file.size)
    instance.image = image_file

    try:
        instance.full_clean()
    except Exception as exc:
        message = "; ".join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        return _error(f"Validation failed: {message}", status=400)

    instance.save()

    log_event(
        AuditLog.EventType.IMAGE_UPLOADED,
        user=request.user,
        request=request,
        description="User uploaded an image.",
        reference_model='UploadedImage',
        reference_id=instance.id)

    return _success("Image uploaded successfully.", data=UploadedImageSerializer(instance).data, status=201)