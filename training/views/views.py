from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from imaging.models import Dataset

from ..models import ModelVersion, TrainingJob


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def training_dashboard_view(request):
    jobs = TrainingJob.objects.select_related('dataset').all()[:25]
    model_versions = ModelVersion.objects.select_related('dataset').all()[:25]
    datasets = Dataset.objects.all()
    return render(request, 'training/dashboard.html', {
        'jobs': jobs,
        'model_versions': model_versions,
        'datasets': datasets,
    })


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def training_job_detail_view(request, job_id):
    job = get_object_or_404(TrainingJob, pk=job_id)
    return render(request, 'training/job_detail.html', {'job': job})
