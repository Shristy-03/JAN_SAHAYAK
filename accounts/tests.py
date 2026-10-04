from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import EmailVerificationToken, User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountFlowTests(TestCase):
    def test_citizen_registration_creates_inactive_unverified_user(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('accounts:register'), {
                'username': 'newcitizen', 'first_name': 'New', 'last_name': 'Citizen',
                'email': 'newcitizen@example.test', 'password1': 'StrongTestPassword123!',
                'password2': 'StrongTestPassword123!',
            })

        user = User.objects.get(username='newcitizen')
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_email_verification_activates_user(self):
        user = User.objects.create_user(
            username='verificationuser', email='verification@example.test',
            password='StrongTestPassword123!', role=User.Role.CITIZEN, is_active=False,
        )
        token = EmailVerificationToken.objects.create(user=user)
        response = self.client.get(reverse('accounts:verify_email', kwargs={'token': token.token}))

        user.refresh_from_db()
        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)

    def test_login_accepts_email_and_rejects_inactive_user(self):
        active = User.objects.create_user(
            username='activeuser', email='active@example.test', password='StrongTestPassword123!',
            role=User.Role.CITIZEN, is_active=True, email_verified=True,
        )
        inactive = User.objects.create_user(
            username='inactiveuser', email='inactive@example.test', password='StrongTestPassword123!',
            role=User.Role.CITIZEN, is_active=False,
        )
        response = self.client.post(reverse('accounts:login'), {'username': active.email, 'password': 'StrongTestPassword123!'})
        self.assertRedirects(response, reverse('accounts:profile'))
        self.client.logout()
        rejected = self.client.post(reverse('accounts:login'), {'username': inactive.email, 'password': 'StrongTestPassword123!'})
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, 'Please enter a correct')
