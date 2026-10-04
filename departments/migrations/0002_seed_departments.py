from django.db import migrations


DEPARTMENTS = (
    ('Water Department', 'water', 'Handles public water supply and related infrastructure.'),
    ('Electricity Department', 'electricity', 'Handles public electricity infrastructure.'),
    ('Public Works Department', 'public-works', 'Handles roads, drainage, and public infrastructure.'),
    ('Sanitation Department', 'sanitation', 'Handles garbage collection and sanitation matters.'),
    ('Street Lighting Department', 'street-lighting', 'Handles municipal street-lighting issues.'),
)


def seed_departments(apps, schema_editor):
    Department = apps.get_model('departments', 'Department')
    for name, code, description in DEPARTMENTS:
        Department.objects.get_or_create(code=code, defaults={'name': name, 'description': description})


def remove_seed_departments(apps, schema_editor):
    Department = apps.get_model('departments', 'Department')
    Department.objects.filter(code__in=[department[1] for department in DEPARTMENTS]).delete()


class Migration(migrations.Migration):
    dependencies = [('departments', '0001_initial')]

    operations = [migrations.RunPython(seed_departments, remove_seed_departments)]
