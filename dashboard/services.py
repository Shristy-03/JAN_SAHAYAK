from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from complaints.models import Complaint, ComplaintUpdate
from notifications.models import Notification
from notifications.services import schedule_notification


@transaction.atomic
def assign_complaint(*, complaint: Complaint, department, priority: str, actor) -> Complaint:
    """Assign or reassign a complaint while keeping an auditable visible record."""
    previous_department = complaint.assigned_department
    previous_priority = complaint.priority
    complaint.assigned_department = department
    complaint.priority = priority
    complaint.save(update_fields=['assigned_department', 'priority', 'updated_at'])

    changes = []
    if previous_department != department:
        previous_name = previous_department.name if previous_department else 'Unassigned'
        changes.append(f'Assignment changed from {previous_name} to {department.name}.')
    if previous_priority != priority:
        changes.append(f'Priority changed from {previous_priority.title()} to {priority.title()}.')
    if changes:
        ComplaintUpdate.objects.create(
            complaint=complaint,
            author=actor,
            message=' '.join(changes),
            citizen_visible=True,
        )
    if previous_department != department:
        schedule_notification(
            recipient=complaint.citizen,
            complaint=complaint,
            notification_type=Notification.Type.COMPLAINT_ASSIGNED,
            subject=f'Complaint assigned: {complaint.reference_id}',
            body=f'Your complaint "{complaint.title}" has been assigned to {department.name}.',
        )
    return complaint


@transaction.atomic
def queue_overdue_notification(*, complaint: Complaint) -> int:
    """Record urgency notifications for verified officers of an overdue department."""
    if not complaint.is_overdue:
        raise ValidationError('Only overdue complaints can receive an urgency notification.')
    if not complaint.assigned_department_id:
        raise ValidationError('Assign this complaint to a department before notifying officers.')

    recipients = User.objects.filter(
        role=User.Role.OFFICER,
        department=complaint.assigned_department,
        is_active=True,
        email_verified=True,
    )
    cutoff = timezone.now() - timedelta(hours=24)
    queued = 0
    for officer in recipients:
        already_notified = Notification.objects.filter(
            recipient=officer,
            complaint=complaint,
            notification_type=Notification.Type.COMPLAINT_OVERDUE,
            created_at__gte=cutoff,
        ).exists()
        if not already_notified:
            schedule_notification(
                recipient=officer,
                complaint=complaint,
                notification_type=Notification.Type.COMPLAINT_OVERDUE,
                subject=f'Overdue complaint: {complaint.reference_id}',
                body=f'{complaint.reference_id} is overdue and requires urgent attention.',
            )
            queued += 1
    return queued
