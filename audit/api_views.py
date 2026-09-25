from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.decorators import jwt_required, staff_required
from .models import AuditLog
from .serializers import AuditLogSerializer


def _success(message, data=None, status=200):
    return JsonResponse({"status": "success", "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"status": "error", "message": message, "data": data}, status=status)


@require_http_methods(["GET"])
@jwt_required
@staff_required
def audit_log_list_api(request):
    logs_qs = AuditLog.objects.select_related('user').all()

    event_type = request.GET.get('event_type')
    if event_type:
        logs_qs = logs_qs.filter(event_type=event_type)

    try:
        page_number = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 25)), 100)
    except ValueError:
        return _error("page and page_size must be integers.", status=400)

    paginator = Paginator(logs_qs, page_size)
    page_obj = paginator.get_page(page_number)

    return _success(
        "Audit logs retrieved.",
        data={
            "results": AuditLogSerializer(page_obj.object_list, many=True).data,
            "page": page_obj.number,
            "num_pages": paginator.num_pages,
            "count": paginator.count,
        },
    )
