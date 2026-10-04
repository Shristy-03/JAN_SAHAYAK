from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import User
from departments.models import Department

from .models import Complaint, ComplaintCategory, Feedback
from .services import submit_complaint


def image_upload(name='test.png'):
    buffer = BytesIO()
    Image.new('RGB', (2, 2), 'blue').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class ComplaintFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.water = Department.objects.create(name='Water Test Department', code='water-test')
        cls.water_category = ComplaintCategory.objects.create(
            name='Water Test Category', slug='water-test', default_department=cls.water,
        )
        cls.citizen = User.objects.create_user(
            username='citizen', email='citizen@example.test', password='StrongTestPassword123!',
            role=User.Role.CITIZEN, is_active=True, email_verified=True,
        )
        cls.other_citizen = User.objects.create_user(
            username='othercitizen', email='other@example.test', password='StrongTestPassword123!',
            role=User.Role.CITIZEN, is_active=True, email_verified=True,
        )

    def create_complaint(self, citizen=None, **kwargs):
        values = {
            'citizen': citizen or self.citizen, 'category': self.water_category,
            'title': 'Leaking pipe', 'description': 'Water is leaking near the park.',
        }
        values.update(kwargs)
        return submit_complaint(**values)

    def test_complaint_creation_routes_to_department_and_records_history(self):
        self.client.force_login(self.citizen)
        response = self.client.post(reverse('complaints:submit'), {
            'category': self.water_category.pk, 'title': 'Leaking pipe',
            'description': 'Water is leaking near the park.', 'location_text': 'City park',
            'latitude': '19.076000', 'longitude': '72.877700',
        })
        complaint = Complaint.objects.get(citizen=self.citizen)
        self.assertRedirects(response, reverse('complaints:detail', kwargs={'reference_id': complaint.reference_id}))
        self.assertEqual(complaint.assigned_department, self.water)
        self.assertEqual(complaint.status, Complaint.Status.PENDING)
        self.assertEqual(complaint.status_history.count(), 1)
        self.assertEqual(complaint.latitude, Decimal('19.076000'))

    def test_citizen_cannot_view_another_citizens_complaint(self):
        complaint = self.create_complaint()
        self.client.force_login(self.other_citizen)
        response = self.client.get(reverse('complaints:detail', kwargs={'reference_id': complaint.reference_id}))
        self.assertEqual(response.status_code, 404)

    def test_feedback_requires_completion_ownership_and_prevents_duplicates(self):
        complaint = self.create_complaint()
        self.client.force_login(self.citizen)
        before_completion = self.client.post(reverse('complaints:feedback', kwargs={'reference_id': complaint.reference_id}), {'rating': 5, 'comment': 'Quick response.'})
        self.assertEqual(before_completion.status_code, 200)
        self.assertEqual(Feedback.objects.count(), 0)

        complaint.status = Complaint.Status.COMPLETED
        complaint.save(update_fields=['status'])
        self.client.force_login(self.other_citizen)
        forbidden = self.client.post(reverse('complaints:feedback', kwargs={'reference_id': complaint.reference_id}), {'rating': 5, 'comment': 'Not mine.'})
        self.assertEqual(forbidden.status_code, 404)

        self.client.force_login(self.citizen)
        first = self.client.post(reverse('complaints:feedback', kwargs={'reference_id': complaint.reference_id}), {'rating': 5, 'comment': 'Quick response.'})
        duplicate = self.client.post(reverse('complaints:feedback', kwargs={'reference_id': complaint.reference_id}), {'rating': 4, 'comment': 'Duplicate.'})
        self.assertRedirects(first, reverse('complaints:detail', kwargs={'reference_id': complaint.reference_id}))
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Feedback.objects.filter(complaint=complaint).count(), 1)

    def test_overdue_queryset_and_property_ignore_terminal_complaints(self):
        overdue = self.create_complaint()
        overdue.expected_resolution_at = timezone.now() - timedelta(hours=1)
        overdue.save(update_fields=['expected_resolution_at'])
        completed = self.create_complaint(title='Completed issue')
        completed.status = Complaint.Status.COMPLETED
        completed.expected_resolution_at = timezone.now() - timedelta(hours=1)
        completed.save(update_fields=['status', 'expected_resolution_at'])

        self.assertTrue(overdue.is_overdue)
        self.assertFalse(completed.is_overdue)
        self.assertEqual(list(Complaint.objects.overdue()), [overdue])

    def test_uploaded_complaint_images_are_saved(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.citizen)
            response = self.client.post(reverse('complaints:submit'), {
                'category': self.water_category.pk, 'title': 'Photo evidence',
                'description': 'Image attached.', 'images': [image_upload()],
            })
            complaint = Complaint.objects.get(citizen=self.citizen)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(complaint.images.count(), 1)
