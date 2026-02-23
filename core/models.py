from django.db import models
from django.contrib.auth.models import User


class Problem(models.Model):
    CATEGORY_CHOICES = [
        ('Water', 'Water'),
        ('Electricity', 'Electricity'),
        ('Job', 'Job'),
        ('Health', 'Health'),
    ]

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    description = models.TextField()

    def __str__(self):
        return self.category


class Scheme(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    eligibility = models.TextField()
    benefits = models.TextField()

    def __str__(self):
        return self.name


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    area = models.CharField(max_length=200)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint {self.id} - {self.status}"
