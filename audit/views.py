from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from .models import AuditLog


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def audit_log_view(request):
    logs_qs = AuditLog.objects.select_related('user').all()

    event_type = request.GET.get('event_type')
    if event_type:
        logs_qs = logs_qs.filter(event_type=event_type)

    paginator = Paginator(logs_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'event_types': AuditLog.EventType.choices,
        'selected_event_type': event_type or '',
    }
    return render(request, 'audit/audit_log_list.html', context)
