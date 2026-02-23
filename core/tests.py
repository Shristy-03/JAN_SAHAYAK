from django.test import TestCase
from django.contrib.auth.models import User
from .models import Problem, Complaint


class ModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        self.problem = Problem.objects.create(
            category="Water",
            description="Water supply issue"
        )

    def test_problem_creation(self):
        self.assertEqual(self.problem.category, "Water")

    def test_complaint_creation(self):
        complaint = Complaint.objects.create(
            user=self.user,
            problem=self.problem,
            area="Delhi"
        )
        self.assertEqual(complaint.status, "Pending")
