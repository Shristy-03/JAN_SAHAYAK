from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

from .forms import CitizenRegistrationForm, ProfileForm, SignInForm
from .models import EmailVerificationToken
from .services import send_verification_email


class RegisterView(CreateView):
    form_class = CitizenRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            send_verification_email(self.request, self.object)
        messages.success(self.request, 'Your account was created. Verify your email before signing in.')
        return redirect(self.get_success_url())


class SignInView(LoginView):
    authentication_form = SignInForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class SignOutView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        messages.info(request, 'You have been signed out.')
        return redirect('accounts:login')


def profile_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    return render(request, 'accounts/profile.html')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated.')
        return super().form_valid(form)


def verify_email(request: HttpRequest, token) -> HttpResponse:
    verification = get_object_or_404(EmailVerificationToken.objects.select_related('user'), token=token)
    if not verification.is_valid:
        messages.error(request, 'This verification link is invalid, expired, or has already been used.')
        return redirect('accounts:login')

    with transaction.atomic():
        verification.used_at = timezone.now()
        verification.save(update_fields=['used_at'])
        verification.user.email_verified = True
        verification.user.is_active = True
        verification.user.save(update_fields=['email_verified', 'is_active'])
    login(request, verification.user, backend='accounts.backends.EmailOrUsernameModelBackend')
    messages.success(request, 'Your email is verified. Welcome to JAN SAHAYAK.')
    return redirect('accounts:profile')


@require_POST
def resend_verification(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.email_verified:
        messages.info(request, 'Your email address is already verified.')
    else:
        send_verification_email(request, request.user)
        messages.success(request, 'A new verification email has been sent.')
    return redirect('accounts:profile')
