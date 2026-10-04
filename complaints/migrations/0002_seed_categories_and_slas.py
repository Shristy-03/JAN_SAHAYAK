from django.db import migrations


CATEGORIES = (
    ('Water', 'water', 'water'),
    ('Electricity', 'electricity', 'electricity'),
    ('Roads', 'roads', 'public-works'),
    ('Garbage/Sanitation', 'garbage-sanitation', 'sanitation'),
    ('Street Lights', 'street-lights', 'street-lighting'),
    ('Drainage', 'drainage', 'public-works'),
    ('Public Infrastructure', 'public-infrastructure', 'public-works'),
    ('Other', 'other', None),
)

SLAS = (
    ('LOW', 72),
    ('MEDIUM', 72),
    ('HIGH', 24),
    ('URGENT', 24),
)


def seed_categories_and_slas(apps, schema_editor):
    Department = apps.get_model('departments', 'Department')
    ComplaintCategory = apps.get_model('complaints', 'ComplaintCategory')
    ResolutionSLA = apps.get_model('complaints', 'ResolutionSLA')

    for name, slug, department_code in CATEGORIES:
        defaults = {'name': name}
        if department_code:
            defaults['default_department'] = Department.objects.get(code=department_code)
        ComplaintCategory.objects.get_or_create(slug=slug, defaults=defaults)

    for priority, hours in SLAS:
        ResolutionSLA.objects.get_or_create(
            category=None,
            priority=priority,
            defaults={'expected_resolution_hours': hours},
        )


def remove_seed_categories_and_slas(apps, schema_editor):
    ComplaintCategory = apps.get_model('complaints', 'ComplaintCategory')
    ResolutionSLA = apps.get_model('complaints', 'ResolutionSLA')
    ResolutionSLA.objects.filter(category__isnull=True, priority__in=[sla[0] for sla in SLAS]).delete()
    ComplaintCategory.objects.filter(slug__in=[category[1] for category in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('departments', '0002_seed_departments'),
        ('complaints', '0001_initial'),
    ]

    operations = [migrations.RunPython(seed_categories_and_slas, remove_seed_categories_and_slas)]
