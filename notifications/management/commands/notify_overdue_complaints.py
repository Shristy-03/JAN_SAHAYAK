"""Send daily urgency notifications for outstanding overdue complaints.

Run this command from a scheduler today; the invocation can be moved unchanged
to a future Celery task when asynchronous infrastructure is introduced.
"""

from django.core.management.base import BaseCommand

from complaints.models import Complaint
from dashboard.services import queue_overdue_notification


class Command(BaseCommand):
    help = 'Queue at most one overdue urgency notification per officer and complaint every 24 hours.'

    def handle(self, *args, **options):
        complaints = Complaint.objects.overdue().select_related('assigned_department')
        queued = 0
        for complaint in complaints:
            if complaint.assigned_department_id:
                queued += queue_overdue_notification(complaint=complaint)
        self.stdout.write(self.style.SUCCESS(
            f'Processed {complaints.count()} overdue complaint(s); queued {queued} urgency notification(s).'
        ))
