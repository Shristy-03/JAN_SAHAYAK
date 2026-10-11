# JAN SAHAYAK

JAN SAHAYAK is a Django web application for crowdsourced civic-issue reporting and resolution. Citizens submit issues with evidence and location details, departments manage their assigned workload and upload resolution proof, and administrators monitor the complete system through a dedicated dashboard.

## Features

- Email-verified citizen registration, secure login, logout, and profile editing.
- Role-based access for citizens, department officers, and administrators.
- Civic complaint reporting with categories, generated reference IDs, image uploads, location capture, and status timelines.
- Browser geolocation and manual Leaflet point selection using an attributed Esri World Street Map development basemap.
- Department queues scoped strictly to the signed-in officer's department.
- Status, priority, progress-note, resolution-proof, and completion workflow.
- Configurable database-backed resolution SLAs and overdue detection.
- Feedback restricted to the reporting citizen after a complaint is completed.
- Custom admin dashboard with complaint assignment, departments, officers, feedback, urgency notifications, and Chart.js analytics.
- In-app notification records plus email delivery through Django's configured email backend.
- A scheduler-ready overdue-notification command, without Celery or Redis.

## Tech stack

- Python 3.14+
- Django 5.2
- PostgreSQL
- Django templates, Bootstrap 5, HTML/CSS/JavaScript
- Chart.js
- Leaflet and an attributed Esri World Street Map basemap
- Pillow for validated image processing

## Architecture

```text
Citizen -> Complaint -> Assigned Department -> Officer Update -> Resolution Proof -> Completed -> Feedback
                    \-> Status History / Notifications / SLA deadline

Administrator -> Custom dashboard -> Assignment, analytics, overdue monitoring, department management
```

The application uses a custom Django user model. A user has a role (`CITIZEN`, `OFFICER`, or `ADMIN`) and department officers are linked to exactly one department. Complaint categories may define a default department; SLAs are stored in the database by priority and can be overridden by category.

## User roles

| Role | Capabilities |
| --- | --- |
| Citizen | Register, verify email, submit complaints, upload evidence, set location, track progress, view proof, submit feedback. |
| Department officer | View only department-assigned complaints, add updates, change allowed statuses, adjust priority, upload proof, and view feedback. |
| Administrator | Monitor all complaints, manage departments/officers, assign or reassign work, view analytics/feedback, and issue overdue urgency notices. |

## Project structure

```text
JAN_SAHAYAK/
├── accounts/            # Authentication, roles, profile, verification
├── complaints/          # Complaints, images, SLAs, history, feedback
├── config/              # Django settings and root URL configuration
├── dashboard/           # Custom administrator dashboard and analytics
├── departments/         # Department officer workflows
├── notifications/       # Notification delivery service and overdue command
├── static/css/          # Shared responsive civic-service styling
├── templates/           # Reusable base and app templates
├── media/               # Runtime uploads; ignored by Git
├── .env.example         # Environment-variable template
├── requirements.txt
└── manage.py
```

## Prerequisites

- Python 3.14 or later
- PostgreSQL 15 or later
- Git

## PostgreSQL setup

Connect as a PostgreSQL administrator and create a database and application user. Substitute your own secure password; do not put it in source control.

```sql
CREATE USER jan_sahayak_user WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE jan_sahayak OWNER jan_sahayak_user;
```

If you use an existing PostgreSQL user, create the `jan_sahayak` database owned by that user instead.

## Installation

### 1. Create and activate the virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the template and edit the local file:

```powershell
Copy-Item .env.example .env
```

At a minimum, configure these values in `.env`:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_NAME=jan_sahayak
DATABASE_USER=jan_sahayak_user
DATABASE_PASSWORD=choose-a-strong-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

`.env` is intentionally ignored by Git. Never commit real credentials, API keys, or SMTP passwords.

### 4. Apply migrations

```powershell
python manage.py migrate
```

Initial migrations seed five departments, eight civic complaint categories, and default SLA rules:

- Low/medium priority: 72 hours
- High/urgent priority: 24 hours

### 5. Create an administrator

```powershell
python manage.py createsuperuser
```

The superuser can access the custom JAN SAHAYAK administrator dashboard at `/dashboard/` and Django's built-in administration at `/admin/`.

### 6. Run the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Email configuration

Local development uses Django's console email backend if `EMAIL_BACKEND` is empty. Email content appears in the server console and no SMTP credentials are required.

For SMTP delivery, configure the following values in `.env`:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@example.com
```

Email is sent for verification, complaint submission, assignment, status changes, completion, and overdue urgency notifications. Failures are logged and do not roll back a citizen or officer workflow.

## Overdue notifications

The command below finds non-terminal complaints past their SLA deadline and queues at most one urgency notification per officer/complaint in 24 hours.

```powershell
python manage.py notify_overdue_complaints
```

Run it periodically with Windows Task Scheduler, cron, or another scheduler. It is intentionally implemented as a management command so it can later be moved to Celery without changing the underlying overdue logic.

## Tests

The suite runs against a temporary PostgreSQL database named `test_<DATABASE_NAME>`.

```powershell
python manage.py test --verbosity 2
```

The included tests cover registration, verification/login behavior, complaint creation and privacy, department authorization, status/proof completion, feedback permissions and duplicate prevention, administrator access, image handling, and overdue detection.

## Render production deployment

The repository includes `render.yaml`, which provisions a Render Python web service, managed PostgreSQL database, WhiteNoise static-file delivery, Gunicorn, and an hourly Render cron job for overdue notifications. Complaint and resolution images use S3-compatible object storage in production.

1. Push the committed deployment changes to the intended GitHub branch.
2. In Render, create a **New Blueprint Instance** and select that repository and branch.
3. Create an S3-compatible bucket and configure its public delivery endpoint (or a CDN custom domain) before applying the Blueprint. Provide the requested storage variables in Render; no storage credentials belong in GitHub or `.env`.
4. Enter the SMTP variables requested by Render. Do not set them in GitHub or commit them to `.env`.
5. After the first deploy succeeds, open the Render Shell and run `python manage.py createsuperuser`.

The Blueprint generates `SECRET_KEY`, links `DATABASE_URL` to Render PostgreSQL, sets `DEBUG=False`, and enables HTTPS-only cookies and redirects. The service runs migrations in Render's pre-deploy stage, collects static files during its build, and serves the Django WSGI app with Gunicorn. Its health endpoint is `/healthz/`. The cron job invokes `notify_overdue_complaints` hourly; its built-in 24-hour deduplication prevents repeat alerts for the same officer and complaint.

### Render environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django signing secret; generated by the Blueprint. |
| `DEBUG` | Must be `False` in production. |
| `ALLOWED_HOSTS` | Render hostname and any custom domain. |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origin(s) permitted for CSRF-protected form posts. |
| `DATABASE_URL` | Render PostgreSQL connection string; linked automatically by the Blueprint. |
| `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` | Alternative named PostgreSQL settings for non-Render or local deployments. |
| `USE_S3_MEDIA` | Set to `True` in production; activates S3-compatible upload storage. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Credentials with read/write access restricted to the media bucket. |
| `AWS_STORAGE_BUCKET_NAME` | Bucket that stores complaint and resolution images. |
| `AWS_S3_REGION_NAME` | Storage provider region (use the provider's required value). |
| `AWS_S3_ENDPOINT_URL` | S3-compatible endpoint; leave blank only for standard AWS S3. |
| `AWS_S3_CUSTOM_DOMAIN` | Public bucket/CDN domain used to deliver uploaded images. |
| `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` | HTTPS-only security settings. |
| `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | HTTP Strict Transport Security settings. |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_TIMEOUT`, `DEFAULT_FROM_EMAIL` | SMTP notification delivery configuration. |
| `MAP_TILE_URL`, `MAP_TILE_ATTRIBUTION`, `MAP_TILE_MAX_ZOOM` | Optional approved production tile-provider override. The development default is Esri World Street Map with visible attribution. |

Configure the bucket to serve the uploaded media publicly through the bucket endpoint or CDN domain, because existing complaint and proof image links are direct image URLs. Limit the storage credentials to this bucket and do not enable list/delete privileges unless the provider requires them. The application generates unique image names and does not overwrite existing uploads.

### Redeploying

Push a reviewed commit to the branch connected to the Blueprint. Render automatically runs the build, static collection, migrations, health check, and Gunicorn restart. Review the deploy logs and `/healthz/` after every production deploy.

## Security notes

- Django's authentication system and its standard password hashers are used; no MD5 or plaintext password storage is used.
- `SECRET_KEY`, database settings, and SMTP credentials are read from environment variables.
- CSRF middleware is enabled and protected operations use POST requests.
- Complaint detail queries are owner-scoped for citizens and department-scoped for officers.
- Image content, format, file count, and size are validated before files are stored in media.
- Render production configuration enables `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, and HSTS after HTTPS is correctly configured.

## Git and GitHub

Initialize a local repository and inspect its contents before committing:

```powershell
git init
git status
git add .
git status
git commit -m "Initial JAN SAHAYAK application"
```

Before adding a remote, confirm that `.env`, `.venv/`, `media/`, database files, and editor metadata are not staged. To push to your own empty GitHub repository:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/JAN_SAHAYAK.git
git push -u origin main
```

Do not force push and do not add or replace a remote repository without verifying its destination.

## Future enhancements

- Background processing using Celery and Redis
- REST API with Django REST Framework
- ML-assisted priority suggestions
- S3-compatible object storage before horizontally scaling the production service
- Notification preferences and read-state interface
- Stronger production deployment settings, monitoring, and audit reporting
