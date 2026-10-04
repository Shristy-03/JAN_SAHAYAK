from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AdminAccessTests(TestCase):
    def test_only_administrator_can_access_custom_admin_dashboard(self):
        citizen = User.objects.create_user(
            username='dashboardcitizen', email='dashboardcitizen@example.test',
            password='StrongTestPassword123!', role=User.Role.CITIZEN, is_active=True, email_verified=True,
        )
        administrator = User.objects.create_superuser(
            username='dashboardadmin', email='dashboardadmin@example.test', password='StrongTestPassword123!',
        )
        self.client.force_login(citizen)
        denied = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(administrator)
        allowed = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(allowed.status_code, 200)
