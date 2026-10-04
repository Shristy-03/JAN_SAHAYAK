from django.db import transaction

from django.core.exceptions import PermissionDenied, ValidationError

from .models import Complaint, ComplaintCategory, ComplaintImage, ComplaintStatusHistory, Feedback
from notifications.models import Notification
from notifications.services import schedule_notification


@transaction.atomic
def submit_complaint(*, citizen, category: ComplaintCategory, title: str, description: str, location_text='', latitude=None, longitude=None, images=None) -> Complaint:
    """Create a complaint and its first, auditable PENDING status event."""
    if not category.is_active:
        raise ValueError('The selected complaint category is not active.')

    complaint = Complaint.objects.create(
        citizen=citizen,
        category=category,
        assigned_department=category.default_department,
        title=title,
        description=description,
        location_text=location_text,
        latitude=latitude,
        longitude=longitude,
    )
    ComplaintStatusHistory.objects.create(
        complaint=complaint,
        previous_status='',
        status=Complaint.Status.PENDING,
        changed_by=citizen,
        note='Complaint submitted by citizen.',
    )
    for image in images or []:
        ComplaintImage.objects.create(complaint=complaint, image=image)
    schedule_notification(
        recipient=citizen,
        complaint=complaint,
        notification_type=Notification.Type.COMPLAINT_SUBMITTED,
        subject=f'Complaint submitted: {complaint.reference_id}',
        body=(
            f'Your complaint "{complaint.title}" has been submitted with reference '
            f'{complaint.reference_id}. It is currently pending review.'
        ),
    )
    if complaint.assigned_department_id:
        schedule_notification(
            recipient=citizen,
            complaint=complaint,
            notification_type=Notification.Type.COMPLAINT_ASSIGNED,
            subject=f'Complaint assigned: {complaint.reference_id}',
            body=f'Your complaint "{complaint.title}" has been assigned to {complaint.assigned_department.name}.',
        )
    return complaint


@transaction.atomic
def submit_feedback(*, complaint: Complaint, citizen, rating: int, comment: str) -> Feedback:
    """Allow only the reporting citizen to leave one post-resolution feedback entry."""
    if complaint.citizen_id != citizen.id:
        raise PermissionDenied('Only the citizen who reported this complaint can submit feedback.')
    if complaint.status != Complaint.Status.COMPLETED:
        raise ValidationError('Feedback is available after a complaint is completed.')
    if Feedback.objects.filter(complaint=complaint).exists():
        raise ValidationError('Feedback has already been submitted for this complaint.')
    return Feedback.objects.create(complaint=complaint, citizen=citizen, rating=rating, comment=comment)
