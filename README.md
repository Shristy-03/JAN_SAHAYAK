# JAN SAHAYAK

JAN SAHAYAK is a Django web application for crowdsourced civic-issue reporting and resolution. Citizens submit issues with evidence and location details, departments manage their assigned workload and upload resolution proof, and administrators monitor the complete system through a dedicated dashboard.

## Features

- Email-verified citizen registration, secure login, logout, and profile editing.
- Role-based access for citizens, department officers, and administrators.
- Civic complaint reporting with categories, generated reference IDs, image uploads, location capture, and status timelines.
- Browser geolocation and manual Leaflet/OpenStreetMap point selection.
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
- Leaflet and OpenStreetMap
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

## Security notes

- Django's authentication system and its standard password hashers are used; no MD5 or plaintext password storage is used.
- `SECRET_KEY`, database settings, and SMTP credentials are read from environment variables.
- CSRF middleware is enabled and protected operations use POST requests.
- Complaint detail queries are owner-scoped for citizens and department-scoped for officers.
- Image content, format, file count, and size are validated before files are stored in media.
- Enable `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_SSL_REDIRECT` only after HTTPS is correctly configured in deployment.

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
- Object storage for production media
- Notification preferences and read-state interface
- Stronger production deployment settings, monitoring, and audit reporting
