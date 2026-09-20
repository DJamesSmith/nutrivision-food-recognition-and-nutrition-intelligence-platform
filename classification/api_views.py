import logging

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required, log_execution_time
from audit.models import AuditLog
from audit.services import log_event
from imaging.models import UploadedImage
from training.services import get_active_model_version

from .inference import InferenceError, predict_image
from .models import Prediction
from .serializers import PredictionSerializer

logger = logging.getLogger(__name__)


def _success(message, data=None, status=200):
    return JsonResponse({"status": "success", "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"status": "error", "message": message, "data": data}, status=status)


# ==================================================
# POST /api/classification/predict/
# ==================================================

@require_http_methods(["POST"])
@jwt_required
@log_execution_time
def predict_api(request):
    model_version = get_active_model_version()
    if model_version is None:
        return _error(
            "No active trained model is available yet. Please train a model first.",
            status=409,
        )

    image_file = request.FILES.get('image')
    if not image_file:
        return _error("No image file was provided.", status=400)

    # ---- Image Upload + Validation ----
    uploaded_image = UploadedImage(
        user=request.user,
        original_filename=image_file.name,
        content_type=getattr(image_file, 'content_type', '') or '',
        file_size=image_file.size,
    )
    uploaded_image.image = image_file

    try:
        uploaded_image.full_clean()
    except Exception as exc:
        message = "; ".join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        return _error(f"Validation failed: {message}", status=400)

    uploaded_image.save()

    log_event(
        AuditLog.EventType.IMAGE_UPLOADED, user=request.user, request=request,
        description="Image uploaded for prediction.",
        reference_model='UploadedImage', reference_id=uploaded_image.id,
    )

    # ---- Preprocessing -> Load Active Model -> Prediction ----
    try:
        predicted_class, confidence, probabilities = predict_image(
            uploaded_image.image.path, model_version,
        )
    except InferenceError as exc:
        logger.error("Inference failed for user #%s: %s", request.user.id, exc)
        return _error("Prediction failed. Please try again shortly.", status=500)

    # ---- Store Prediction History ----
    prediction = Prediction.objects.create(
        user=request.user,
        uploaded_image=uploaded_image,
        model_version=model_version,
        predicted_class=predicted_class,
        confidence=confidence,
        class_probabilities=probabilities,
    )

    log_event(
        AuditLog.EventType.PREDICTION_CREATED, user=request.user, request=request,
        description=f"Predicted '{predicted_class}' ({confidence:.2%}) using model {model_version.version}.",
        reference_model='Prediction', reference_id=prediction.id,
    )

    return _success(
        "Prediction completed successfully.",
        data=PredictionSerializer(prediction, context={'request': request}).data,
        status=201,
    )


# ==================================================
# GET /api/classification/history/
# ==================================================

@require_http_methods(["GET"])
@jwt_required
def history_api(request):
    # Users only ever see their own predictions, unless they are
    # staff/admin AND explicitly ask for everyone's (?all=true) — server-
    # side enforced, never left to the frontend to decide.
    show_all = request.GET.get('all') == 'true' and (request.user.is_staff or request.user.is_superuser)

    queryset = Prediction.objects.select_related('model_version', 'uploaded_image')
    queryset = queryset.all() if show_all else queryset.filter(user=request.user)

    try:
        page_number = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
    except ValueError:
        return _error("page and page_size must be integers.", status=400)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    return _success(
        "Prediction history retrieved.",
        data={
            "results": PredictionSerializer(page_obj.object_list, many=True, context={'request': request}).data,
            "page": page_obj.number,
            "num_pages": paginator.num_pages,
            "count": paginator.count,
        },
    )
