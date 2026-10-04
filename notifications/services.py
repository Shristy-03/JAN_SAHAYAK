"""Reusable in-app and email notification delivery services."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Notification


logger = logging.getLogger(__name__)


def send_notification(*, recipient, notification_type, subject: str, body: str, complaint=None) -> Notification:
    """Persist a notification and attempt delivery through Django's configured backend."""
    notification = Notification.objects.create(
        recipient=recipient,
        complaint=complaint,
        notification_type=notification_type,
        subject=subject,
        body=body,
    )
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
    except Exception:  # SMTP outages must never block the civic reporting workflow.
        logger.exception('Unable to send notification email for notification %s.', notification.pk)
    else:
        notification.emailed_at = timezone.now()
        notification.save(update_fields=['emailed_at'])
    return notification


def schedule_notification(**kwargs) -> None:
    """Send only after the surrounding database transaction commits successfully."""
    transaction.on_commit(lambda: send_notification(**kwargs))
