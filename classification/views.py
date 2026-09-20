from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .models import Prediction


@never_cache
@login_required(login_url='accounts:login')
def predict_view(request):
    return render(request, 'classification/predict.html')


@never_cache
@login_required(login_url='accounts:login')
def history_view(request):
    # Users only ever see their own history here — broader access (e.g.
    # staff reviewing everyone's predictions) is exposed separately via
    # the API's ?all=true flag, gated on is_staff/is_superuser.
    queryset = Prediction.objects.filter(user=request.user).select_related('model_version')
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'classification/history.html', {'page_obj': page_obj})