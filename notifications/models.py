from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An auditable in-app and email notification for a system event."""

    class Type(models.TextChoices):
        EMAIL_VERIFICATION = 'EMAIL_VERIFICATION', 'Email verification'
        COMPLAINT_SUBMITTED = 'COMPLAINT_SUBMITTED', 'Complaint submitted'
        COMPLAINT_ASSIGNED = 'COMPLAINT_ASSIGNED', 'Complaint assigned'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Status changed'
        COMPLAINT_COMPLETED = 'COMPLAINT_COMPLETED', 'Complaint completed'
        COMPLAINT_OVERDUE = 'COMPLAINT_OVERDUE', 'Complaint overdue'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    complaint = models.ForeignKey('complaints.Complaint', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=25, choices=Type.choices)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    emailed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('recipient', 'is_read', '-created_at'))]
