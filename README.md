# NETCAREER

A robust, scalable backend for a LinkedIn-like professional networking platform built with Django REST Framework. This platform connects job seekers with employers, facilitates professional networking, and provides a comprehensive job search experience.

[![Django](https://img.shields.io/badge/Django-4.2.7-green)](https://docs.djangoproject.com/en/4.2/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-blue)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/docs/15/index.html)
[![Redis](https://img.shields.io/badge/Redis-7-red)](https://redis.io/docs/)
[![Celery](https://img.shields.io/badge/Celery-5.3-green)](https://docs.celeryq.dev/)
[![Swagger UI](https://img.shields.io/badge/Swagger%20UI-API%20Docs-brightgreen)](https://swagger.io/tools/swagger-ui/)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%2520Actions-success)](https://docs.github.com/actions)

# Features
## User Management
- Role-based authentication (Job Seeker, Employer, Admin)
- JWT token-based authentication
- User profiles with professional experience and education
- Profile verification system

## Job Platform
- Job posting and management for employers
- Advanced job search with filtering
- Job applications with status tracking
- Save jobs for later application
- Resume upload and management
## Professional Networking
- ##### Connection system with request/accept workflow
- Professional profile viewing
- Skill endorsements (extensible)
- Company following system
## Content & Engagement
- Professional pots with rich media support
- Likes,comments and shares
- Feed algorithm for personalized content
- Post visibility controls (public/connections/private)
## Company Pages
- Company profile management
- Company updates and posts
- Follower system

# Architecture
```text
NetCareer/
├── backend/                 # Django Project Root
│   ├── apps/               # Modular Applications
│   │   ├── users/          # Authentication & User Management
│   │   ├── profiles/       # Professional Profiles
│   │   ├── companies/      # Company Management
│   │   ├── jobs/           # Job Platform
│   │   ├── connections/    # Networking & Connections
│   │   ├── posts/          # Content & Engagement
│   │   ├── notifications/  # Notification System
│   │   └── common/         # Shared Utilities
│   ├── config/             # Project Configuration
│   └── core/               # Core Utilities & Middleware
├                 
## Getting Started

You can run locally with Docker (recommended) or with a Python virtualenv.

### Prerequisites
- Docker and Docker Compose
- Or Python 3.14 with virtualenv

### Environment
Create a `.env` with at least:

```env
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=you@example.com
REDIS_URL=redis://localhost:6379/1
```

### Run with Docker

```bash
cd backend
docker compose up --build
```

### Run locally (virtualenv)

```bash
# macOS zsh
python3 -m venv nvenv
source nvenv/bin/activate
pip install -r backend/requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings
cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Authentication

JWT-based auth with email verification. See `backend/docs/api/authentication.md` for full endpoint details and curl examples.

Key endpoints:
- `POST /auth/register/`
- `GET /auth/verify-email/?token=...`
- `POST /auth/login/`
- `POST /auth/logout/`
- `GET|PATCH /profile/`

## Development

- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Superuser: `python manage.py createsuperuser`
- Celery workers configured in `backend/config/celery.py`

## License

MIT — see `LICENSE`.
├── docs/                   # API Documentation
