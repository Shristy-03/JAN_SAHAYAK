from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from complaints.models import Complaint, ComplaintCategory, ResolutionProof
from complaints.services import submit_complaint

from .models import Department


def proof_upload():
    buffer = BytesIO()
    Image.new('RGB', (2, 2), 'green').save(buffer, format='PNG')
    return SimpleUploadedFile('proof.png', buffer.getvalue(), content_type='image/png')


class DepartmentAuthorizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.water = Department.objects.create(name='Water Department Test', code='water-department-test')
        cls.electricity = Department.objects.create(name='Electricity Department Test', code='electricity-department-test')
        cls.category = ComplaintCategory.objects.create(name='Water Category Test', slug='water-category-test', default_department=cls.water)
        cls.citizen = User.objects.create_user(username='reporter', email='reporter@example.test', password='StrongTestPassword123!', role=User.Role.CITIZEN, is_active=True, email_verified=True)
        cls.water_officer = User.objects.create_user(username='waterofficer', email='waterofficer@example.test', password='StrongTestPassword123!', role=User.Role.OFFICER, department=cls.water, is_active=True, email_verified=True)
        cls.electricity_officer = User.objects.create_user(username='electricityofficer', email='electricityofficer@example.test', password='StrongTestPassword123!', role=User.Role.OFFICER, department=cls.electricity, is_active=True, email_verified=True)

    def create_complaint(self):
        return submit_complaint(citizen=self.citizen, category=self.category, title='Water main break', description='Repair needed.')

    def test_officer_cannot_access_or_update_other_department_complaints(self):
        complaint = self.create_complaint()
        self.client.force_login(self.electricity_officer)
        detail = self.client.get(reverse('departments:complaint_detail', kwargs={'reference_id': complaint.reference_id}))
        update = self.client.post(reverse('departments:complaint_update', kwargs={'reference_id': complaint.reference_id}), {
            'status': Complaint.Status.IN_PROGRESS, 'priority': Complaint.Priority.HIGH, 'note': 'Should fail.',
        })
        complaint.refresh_from_db()
        self.assertEqual(detail.status_code, 404)
        self.assertEqual(update.status_code, 404)
        self.assertEqual(complaint.status, Complaint.Status.PENDING)

    def test_status_updates_and_resolution_proof_requirement(self):
        complaint = self.create_complaint()
        self.client.force_login(self.water_officer)
        incomplete = self.client.post(reverse('departments:complaint_update', kwargs={'reference_id': complaint.reference_id}), {
            'status': Complaint.Status.COMPLETED, 'priority': Complaint.Priority.MEDIUM, 'note': 'No proof.',
        })
        self.assertEqual(incomplete.status_code, 400)

        in_progress = self.client.post(reverse('departments:complaint_update', kwargs={'reference_id': complaint.reference_id}), {
            'status': Complaint.Status.IN_PROGRESS, 'priority': Complaint.Priority.HIGH, 'note': 'Team dispatched.', 'citizen_visible': 'on',
        })
        complaint.refresh_from_db()
        self.assertEqual(in_progress.status_code, 302)
        self.assertEqual(complaint.status, Complaint.Status.IN_PROGRESS)
        self.assertEqual(complaint.priority, Complaint.Priority.HIGH)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            proof = self.client.post(reverse('departments:resolution_proof_upload', kwargs={'reference_id': complaint.reference_id}), {
                'image': proof_upload(), 'description': 'Repaired pipe.',
            })
            self.assertEqual(proof.status_code, 302)
            self.assertEqual(ResolutionProof.objects.filter(complaint=complaint).count(), 1)

        completed = self.client.post(reverse('departments:complaint_update', kwargs={'reference_id': complaint.reference_id}), {
            'status': Complaint.Status.COMPLETED, 'priority': Complaint.Priority.HIGH, 'note': 'Work complete.', 'citizen_visible': 'on',
        })
        complaint.refresh_from_db()
        self.assertEqual(completed.status_code, 302)
        self.assertEqual(complaint.status, Complaint.Status.COMPLETED)
