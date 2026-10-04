from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerificationToken, User
from notifications.models import Notification
from notifications.services import schedule_notification


def create_verification_token(user: User) -> EmailVerificationToken:
    """Invalidate outstanding links and return a new one-time verification token."""
    user.verification_tokens.filter(used_at__isnull=True).update(used_at=timezone.now())
    return EmailVerificationToken.objects.create(user=user)


def send_verification_email(request, user: User) -> None:
    token = create_verification_token(user)
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': token.token})
    )
    message = render_to_string(
        'emails/email_verification.txt',
        {'user': user, 'verification_url': verification_url},
    )
    schedule_notification(
        recipient=user,
        notification_type=Notification.Type.EMAIL_VERIFICATION,
        subject='Verify your JAN SAHAYAK email address',
        body=message,
    )
