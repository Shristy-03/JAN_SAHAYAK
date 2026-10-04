from django.db import models


class Department(models.Model):
    """A civic service department responsible for resolving complaints."""

    name = models.CharField(max_length=150, unique=True)
    code = models.SlugField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=25, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'department'
        verbose_name_plural = 'departments'

    def __str__(self) -> str:
        return self.name
