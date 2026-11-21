from django.contrib import messages
from django.contrib.auth import login as sign_in, logout as sign_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from django.views.csrf import csrf_failure as default_csrf_failure

from .forms import LoginForm, ProfileForm, SignupForm
from .models import Profile


class SignInView(LoginView):
    template_name = "core/login.html"
    authentication_form = LoginForm


@require_http_methods(["GET", "POST"])
def signup(request):
    form = SignupForm(request.POST if request.method == "POST" else None)
    if form.is_valid():
        sign_in(request, form.save())
        return redirect("questions:index")
    return render(request, "core/signup.html", {"form": form})


@login_required
@require_POST
def logout(request):
    destination = request.POST.get("next", "")
    sign_out(request)
    if url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure()):
        return redirect(destination)
    return redirect("questions:index")


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    instance = getattr(request.user, "profile", None) or Profile(user=request.user)
    data = request.POST if request.method == "POST" else None
    form = ProfileForm(data, request.FILES, user=request.user, instance=instance)
    avatar_url = instance.avatar_url
    # При ошибке показываем сохранённый аватар, а не ещё не записанный файл.
    if form.is_valid():
        form.save()
        messages.success(request, "Профиль сохранён.")
        return redirect("core:profile")
    return render(request, "core/profile.html", {"form": form, "avatar_url": avatar_url})


def csrf_failure(request, reason=""):
    match = request.resolver_match
    if match and match.namespace == "questions" and match.url_name.startswith("ajax_"):
        return JsonResponse({"error": "Сессия формы устарела. Обновите страницу и повторите действие."}, status=403)
    return default_csrf_failure(request, reason=reason)
