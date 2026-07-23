# 🔍 WHOIS Tracker

An automated domain intelligence platform that tracks WHOIS/RDAP records over time, detects changes, and provides a REST API + web dashboard. Built on **Django 6**, **Django Ninja**, **HTTPX**, and **Django-Q2**.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [How the Change Detection Works](#how-the-change-detection-works)
- [Configuration](#configuration)

---

## Features

- 🌐 **Track any domain** — add domains and get their RDAP data captured immediately
- 🔔 **Change detection** — SHA-256 hashing ensures a new snapshot is only stored when the underlying WHOIS data actually changes
- ⏱ **Automated daily checks** — Django-Q2 cron job dispatches background lookups at midnight UTC
- ⚡ **Manual checks** — trigger an on-demand RDAP lookup from the dashboard or API
- 📋 **Snapshot history** — full timeline of every captured state with expandable raw JSON
- 🔒 **Per-user isolation** — each user only sees and manages their own domains
- 📖 **Auto-generated Swagger UI** — Django Ninja produces interactive API docs at `/api/v1/docs`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser / Client                         │
│                                                                 │
│   http://localhost:8000/          (Frontend – Django Templates) │
│   http://localhost:8000/api/v1/   (REST API  – Django Ninja)    │
│   http://localhost:8000/api/v1/docs  (Swagger UI)              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────────────┐
│                      Django 6 Application                       │
│                                                                 │
│  ┌─────────────────┐   ┌──────────────────┐  ┌──────────────┐  │
│  │  Django Ninja   │   │  Django Views    │  │ Django Admin │  │
│  │  (API Layer)    │   │  (Template HTML) │  │  /admin/     │  │
│  └────────┬────────┘   └──────────────────┘  └──────────────┘  │
│           │                                                     │
│  ┌────────▼────────────────────────────────────────────────┐   │
│  │                    tracker/services.py                   │   │
│  │                                                          │   │
│  │  fetch_rdap_payload()  →  HTTPX  →  rdap.org/domain/... │   │
│  │  process_domain_check() →  SHA-256 diff  →  ORM write   │   │
│  └────────┬────────────────────────────────────────────────┘   │
│           │                                                     │
│  ┌────────▼───────────────────────────────────────────────┐    │
│  │                      Django ORM                        │    │
│  │   TrackedDomain   ──┐                                  │    │
│  │   WhoisSnapshot   ◄─┘  (SQLite / PostgreSQL)           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Django-Q2 Worker                      │  │
│  │                                                          │  │
│  │  dispatch_daily_whois_checks()  ← DAILY CRON (midnight)  │  │
│  │       └─ async_task(process_domain_check, domain_id)     │  │
│  │                                                          │  │
│  │  On new domain add → async_task fires immediately        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Web Framework | Django 6 | ORM, auth, migrations, admin, templating |
| API Layer | Django Ninja 1.x | FastAPI-style type-safe routing, Swagger UI |
| Data Ingestion | HTTPX | Async-ready HTTP client for RDAP queries |
| Task Scheduler | Django-Q2 | Database-backed background jobs & cron |
| Database | SQLite (dev) / PostgreSQL (prod) | Persistence |
| Frontend | Vanilla HTML/CSS/JS | Dark-mode SPA-like templates calling the API |

---

## Project Structure

```
whois_tracker_django/
│
├── config/                   # Django project configuration
│   ├── settings.py           # All settings (DB, Q_CLUSTER, auth redirects, etc.)
│   ├── urls.py               # Root URL routing (admin, API, frontend)
│   └── wsgi.py
│
├── tracker/                  # Core application
│   ├── models.py             # TrackedDomain + WhoisSnapshot ORM models
│   ├── admin.py              # Django Admin registration
│   ├── api.py                # Django Ninja endpoints (CRUD + manual check + snapshots)
│   ├── services.py           # RDAP fetch + SHA-256 diff + snapshot persistence
│   ├── tasks.py              # Daily cron dispatcher (dispatch_daily_whois_checks)
│   ├── views.py              # Django views serving the HTML templates
│   └── migrations/           # Auto-generated database migrations
│
├── templates/
│   └── tracker/
│       ├── login.html        # Login page (glassmorphism UI)
│       ├── dashboard.html    # Domain grid dashboard
│       └── domain_detail.html # Snapshot history timeline
│
├── static/                   # Static files directory (CSS/JS if extracted)
├── manage.py
├── requirements.txt          # (generate with: pip freeze > requirements.txt)
└── .gitignore
```

### Key Models

```
TrackedDomain
├── user          → ForeignKey(User)     # per-user isolation
├── domain_name   → CharField            # e.g. "google.com"
├── is_active     → BooleanField         # pauses tracking when False
└── created_at    → DateTimeField

WhoisSnapshot
├── domain        → ForeignKey(TrackedDomain)
├── payload_hash  → CharField(64)        # SHA-256 of the sorted RDAP JSON
├── raw_json      → TextField            # full RDAP response
└── checked_at    → DateTimeField
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip
- (Optional) PostgreSQL for production

### 1. Clone & create virtual environment

```powershell
git clone <your-repo-url>
cd whois_tracker_django

python -m venv venv
.\venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate     # macOS / Linux
```

### 2. Install dependencies

```powershell
pip install django django-ninja httpx django-q2 psycopg2-binary
```

Or if you have a `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### 3. Apply database migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

This creates all tables including Django's built-in auth, the Django-Q2 job queue tables, and the `tracker` app tables.

### 4. Create a superuser

```powershell
python manage.py createsuperuser
```

### 5. Register the daily cron schedule

Run this once to insert the midnight schedule into the database:

```powershell
python manage.py shell -c "
import datetime
from django_q.models import Schedule
Schedule.objects.get_or_create(
    func='tracker.tasks.dispatch_daily_whois_checks',
    defaults={
        'schedule_type': Schedule.DAILY,
        'repeats': -1,
        'next_run': datetime.datetime(2026, 7, 25, 0, 0, 0, tzinfo=datetime.timezone.utc)
    }
)
print('Schedule registered.')
"
```

---

## Running the Application

You need **two terminal processes** running simultaneously.

### Terminal 1 — Django development server

```powershell
.\venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2 — Django-Q2 background worker

```powershell
.\venv\Scripts\activate
python manage.py qcluster
```

The `qcluster` worker is required for:
- Processing the **immediate RDAP check** fired when a new domain is added
- Executing the **daily midnight cron** for all active domains

> **Note:** Without the worker running, domains will be added to the database but no WHOIS snapshots will be fetched.

---

## API Reference

Base URL: `http://127.0.0.1:8000/api/v1/`

**Authentication:** All endpoints require an active Django session (log in via `/login/` or `/admin/` first). CSRF token must be sent as the `X-CSRFToken` header for non-GET requests.

Interactive Swagger docs: `http://127.0.0.1:8000/api/v1/docs`

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/domains/` | Add a domain to track (fires immediate WHOIS check) |
| `GET` | `/domains/` | List all domains for the authenticated user |
| `DELETE` | `/domains/{id}/` | Remove a domain and all its snapshots |
| `POST` | `/domains/{id}/check` | Trigger an on-demand RDAP lookup |
| `GET` | `/domains/{id}/snapshots/` | List all snapshots for a domain (includes raw JSON) |

### Example: Add a domain

```bash
curl -X POST http://127.0.0.1:8000/api/v1/domains/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <your-csrf-token>" \
  -b "sessionid=<your-session-id>" \
  -d '{"domain_name": "example.com"}'
```

Response:
```json
{
  "id": 1,
  "domain_name": "example.com",
  "is_active": true,
  "created_at": "2026-07-24T00:00:00+00:00",
  "snapshot_count": 0
}
```

> The snapshot count will update to `1` within a few seconds as the background worker fetches the RDAP data.

---

## Frontend

| URL | Page |
|---|---|
| `http://127.0.0.1:8000/` | Redirects to dashboard (or login) |
| `http://127.0.0.1:8000/login/` | Login page |
| `http://127.0.0.1:8000/dashboard/` | Domain management dashboard |
| `http://127.0.0.1:8000/domains/{id}/` | Snapshot history for a specific domain |
| `http://127.0.0.1:8000/admin/` | Django Admin panel |
| `http://127.0.0.1:8000/api/v1/docs` | Swagger / OpenAPI UI |

The frontend is built with vanilla HTML, CSS, and JavaScript. All data is fetched client-side via the Ninja API endpoints using the session cookie set at login. No JavaScript framework or build step is required.

---

## How the Change Detection Works

```
1. HTTPX fetches RDAP JSON from https://rdap.org/domain/<name>
2. JSON is serialized with sorted keys (deterministic output)
3. SHA-256 hash is computed over the serialized bytes
4. Most recent snapshot hash is compared to the new hash
5. If hashes differ  → new WhoisSnapshot is saved to the database
6. If hashes match   → nothing is written (no-op)
```

This means the snapshot table is an **append-only log of changes** — every row represents a genuine state change in the domain's WHOIS record.

---

## Configuration

All settings live in [`config/settings.py`](config/settings.py).

### Django-Q2 worker settings

```python
Q_CLUSTER = {
    "name": "whois_worker",
    "workers": 2,          # parallel worker processes
    "recycle": 500,        # restart worker after N tasks (memory safety)
    "timeout": 60,         # task timeout in seconds
    "compress": True,      # compress task payloads in the DB
    "save_limit": 250,     # keep last N completed tasks
    "queue_limit": 500,    # max queued tasks before blocking
    "orm": "default",      # use the Django DB as the broker (no Redis needed)
}
```

### Switching to PostgreSQL (production)

Replace the `DATABASES` block in `settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "whois_tracker",
        "USER": "postgres",
        "PASSWORD": "yourpassword",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

Then run `python manage.py migrate` to apply all migrations to the new database.
