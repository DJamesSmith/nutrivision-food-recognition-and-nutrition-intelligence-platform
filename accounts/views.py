import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegistrationForm
from .signals import login_failed, user_logged_in_custom, user_logged_out_custom, user_registered
from .utils import generate_access_token, generate_refresh_token, set_jwt_cookies, unset_jwt_cookies

logger = logging.getLogger(__name__)


def home_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'accounts/home.html')


@never_cache
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_registered.send(sender=register_view, user=user, request=request)
            logger.info("New user registered: %s", user.email)
            messages.success(request, "Registration successful. Please log in.")
            return redirect('accounts:login')
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']
            user = authenticate(request, identifier=identifier, password=password)
            if user is not None:
                login(request, user)
                user_logged_in_custom.send(sender=login_view, user=user, request=request)
                messages.success(request, f"Welcome back, {user.get_short_name()}.")

                # Session pages that make jQuery AJAX/FormData calls against JWT-protected API endpoints (e.g. imaging dataset uploads)
                # need a JWT cookie too, so issue one alongside the session cookie at the same login step. The two auth mechanisms
                # remain independent — this only sets both cookies at once.
                response = redirect('accounts:dashboard')
                access_token = generate_access_token(user)
                refresh_token = generate_refresh_token(user)
                return set_jwt_cookies(response, access_token, refresh_token)

            login_failed.send(sender=login_view, identifier=identifier, request=request)
            messages.error(request, "Invalid credentials. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@never_cache
@login_required(login_url='accounts:login')
@require_http_methods(["POST", "GET"])
def logout_view(request):
    user = request.user
    logout(request)
    user_logged_out_custom.send(sender=logout_view, user=user, request=request)
    messages.info(request, "You have been logged out.")
    response = redirect('accounts:login')
    return unset_jwt_cookies(response)


@never_cache
@login_required(login_url='accounts:login')
def dashboard_view(request):
    context = {
        'user': request.user,
        # Populated with real data once the imaging/training/classification
        # apps exist (Phases 3-5): total_predictions, latest_model, etc.
    }
    return render(request, 'accounts/dashboard.html', context)
