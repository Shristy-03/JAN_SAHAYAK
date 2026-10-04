import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone


def default_verification_expiry():
    return timezone.now() + timedelta(days=2)


class User(AbstractUser):
    """Application user with a role and optional departmental assignment."""

    class Role(models.TextChoices):
        CITIZEN = 'CITIZEN', 'Citizen'
        OFFICER = 'OFFICER', 'Department officer'
        ADMIN = 'ADMIN', 'Administrator'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.CITIZEN)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        related_name='officers',
        null=True,
        blank=True,
    )
    email_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(role='OFFICER') | Q(department__isnull=False),
                name='officer_requires_department',
            ),
        ]
        indexes = [models.Index(fields=('role', 'is_active'))]

    @property
    def is_department_officer(self) -> bool:
        return self.role == self.Role.OFFICER and self.department_id is not None

    @property
    def is_administrator(self) -> bool:
        return self.is_superuser or self.role == self.Role.ADMIN


class EmailVerificationToken(models.Model):
    """One-time, expiring token used to verify a user's email address."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField(default=default_verification_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at >= timezone.now()
