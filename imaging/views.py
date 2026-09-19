from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from .forms import DatasetForm
from .models import Dataset


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def dataset_list_view(request):
    datasets = Dataset.objects.all()
    return render(request, 'imaging/dataset_list.html', {'datasets': datasets})


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def dataset_create_view(request):
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.created_by = request.user
            dataset.save()
            messages.success(request, f"Dataset '{dataset.name}' created.")
            return redirect('imaging:dataset_detail', dataset_id=dataset.id)
        messages.error(request, "Please correct the errors below.")
    else:
        form = DatasetForm()

    return render(request, 'imaging/dataset_form.html', {'form': form})


@never_cache
@login_required(login_url='accounts:login')
@user_passes_test(_is_staff, login_url='accounts:dashboard')
def dataset_detail_view(request, dataset_id):
    dataset = get_object_or_404(Dataset, pk=dataset_id)
    images = dataset.images.select_related('uploaded_by').all()[:200]
    return render(request, 'imaging/dataset_detail.html', {
        'dataset': dataset,
        'images': images,
        'class_distribution': dataset.get_class_distribution(),
    })
