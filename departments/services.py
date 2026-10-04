from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from complaints.models import Complaint, ComplaintStatusHistory, ComplaintUpdate
from notifications.models import Notification
from notifications.services import schedule_notification


ALLOWED_TRANSITIONS = {
    Complaint.Status.PENDING: {Complaint.Status.IN_PROGRESS, Complaint.Status.REJECTED},
    Complaint.Status.IN_PROGRESS: {Complaint.Status.COMPLETED, Complaint.Status.REJECTED},
    Complaint.Status.COMPLETED: set(),
    Complaint.Status.REJECTED: set(),
}


@transaction.atomic
def update_department_complaint(*, complaint: Complaint, actor, status: str, priority: str, note: str, citizen_visible: bool):
    """Apply an authorized officer update and retain a complete audit history."""
    if not actor.is_superuser and actor.department_id != complaint.assigned_department_id:
        raise PermissionDenied('You cannot manage complaints assigned to another department.')

    previous_status = complaint.status
    previous_priority = complaint.priority
    if status != previous_status and status not in ALLOWED_TRANSITIONS[previous_status]:
        raise ValidationError('This complaint cannot be moved to the requested status.')
    if status == Complaint.Status.COMPLETED and not complaint.resolution_proofs.exists():
        raise ValidationError('A resolution proof image is required before completion.')

    complaint.status = status
    complaint.priority = priority
    complaint.save(update_fields=['status', 'priority', 'updated_at'])

    if status != previous_status:
        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=previous_status,
            status=status,
            changed_by=actor,
            note=note,
        )

    update_message = note
    if priority != previous_priority:
        priority_message = f'Priority updated from {previous_priority.title()} to {priority.title()}.'
        update_message = f'{priority_message} {note}'.strip()
    if update_message and (status == previous_status or priority != previous_priority):
        ComplaintUpdate.objects.create(
            complaint=complaint,
            author=actor,
            message=update_message,
            citizen_visible=citizen_visible,
        )
    if status != previous_status:
        if status == Complaint.Status.COMPLETED:
            subject = f'Complaint completed: {complaint.reference_id}'
            body = f'Your complaint "{complaint.title}" has been marked completed. You can now review the resolution proof and submit feedback.'
            notification_type = Notification.Type.COMPLAINT_COMPLETED
        else:
            subject = f'Complaint status updated: {complaint.reference_id}'
            body = f'Your complaint "{complaint.title}" is now {complaint.get_status_display()}.'
            notification_type = Notification.Type.STATUS_CHANGED
        schedule_notification(
            recipient=complaint.citizen,
            complaint=complaint,
            notification_type=notification_type,
            subject=subject,
            body=body,
        )
    return complaint
