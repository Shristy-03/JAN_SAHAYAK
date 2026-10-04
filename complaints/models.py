import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def generate_complaint_reference() -> str:
    return f'JS-{uuid.uuid4().hex[:12].upper()}'


def complaint_image_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f'complaints/{instance.complaint.reference_id}/{uuid.uuid4().hex}{extension}'


def resolution_proof_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f'resolutions/{instance.complaint.reference_id}/{uuid.uuid4().hex}{extension}'


class ComplaintCategory(models.Model):
    """Extensible classification and routing metadata for civic complaints."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    default_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        related_name='default_categories',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'complaint categories'

    def __str__(self) -> str:
        return self.name


class ResolutionSLA(models.Model):
    """Configurable expected resolution time, in hours, for a priority/category."""

    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.CASCADE,
        related_name='resolution_slas',
        null=True,
        blank=True,
        help_text='Leave blank to define a default SLA for this priority.',
    )
    priority = models.CharField(max_length=10, choices=(
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ))
    expected_resolution_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('category__name', 'priority')
        indexes = [models.Index(fields=('category', 'priority', 'is_active'))]

    @classmethod
    def hours_for(cls, category: ComplaintCategory, priority: str) -> int:
        """Prefer a category SLA, then use the configured priority default."""
        sla = cls.objects.filter(category=category, priority=priority, is_active=True).first()
        if sla is None:
            sla = cls.objects.filter(category__isnull=True, priority=priority, is_active=True).first()
        if sla is None:
            raise ValidationError('No active resolution SLA is configured for this complaint priority.')
        return sla.expected_resolution_hours

    def __str__(self) -> str:
        scope = self.category.name if self.category_id else 'All categories'
        return f'{scope}: {self.get_priority_display()} ({self.expected_resolution_hours} hours)'


class ComplaintQuerySet(models.QuerySet):
    def overdue(self):
        return self.filter(expected_resolution_at__lt=timezone.now()).exclude(
            status__in=(Complaint.Status.COMPLETED, Complaint.Status.REJECTED)
        )

    def assigned_to_department(self, department):
        return self.filter(assigned_department=department)


class Complaint(models.Model):
    """A citizen report and its current assignment, state, and resolution deadline."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        REJECTED = 'REJECTED', 'Rejected'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    reference_id = models.CharField(max_length=20, unique=True, editable=False, default=generate_complaint_reference)
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    category = models.ForeignKey(ComplaintCategory, on_delete=models.PROTECT, related_name='complaints')
    assigned_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        related_name='complaints',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    location_text = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    expected_resolution_at = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ComplaintQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('citizen', '-created_at')),
            models.Index(fields=('assigned_department', 'status', '-created_at')),
            models.Index(fields=('status', 'priority', '-created_at')),
            models.Index(fields=('expected_resolution_at', 'status')),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(Q(latitude__isnull=True, longitude__isnull=True) | Q(latitude__isnull=False, longitude__isnull=False)),
                name='complaint_location_coordinates_together',
            ),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding and not self.expected_resolution_at:
            hours = ResolutionSLA.hours_for(self.category, self.priority)
            self.expected_resolution_at = timezone.now() + timedelta(hours=hours)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        return self.status not in {self.Status.COMPLETED, self.Status.REJECTED} and self.expected_resolution_at < timezone.now()

    def __str__(self) -> str:
        return f'{self.reference_id}: {self.title}'


class ComplaintImage(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=complaint_image_upload_to)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('uploaded_at',)


class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=15, choices=Complaint.Status.choices, blank=True)
    status = models.CharField(max_length=15, choices=Complaint.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='status_changes',
        null=True,
        blank=True,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        indexes = [models.Index(fields=('complaint', 'created_at'))]


class ComplaintUpdate(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='complaint_updates')
    message = models.TextField()
    citizen_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        indexes = [models.Index(fields=('complaint', 'citizen_visible', 'created_at'))]


class ResolutionProof(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='resolution_proofs')
    image = models.ImageField(upload_to=resolution_proof_upload_to)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='resolution_proofs')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('uploaded_at',)


class Feedback(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='feedback')
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback_entries')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('citizen', '-created_at'))]

    def clean(self):
        if self.complaint_id and self.citizen_id and self.complaint.citizen_id != self.citizen_id:
            raise ValidationError({'citizen': 'Only the complaint reporter can submit feedback.'})
