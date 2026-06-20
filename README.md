# TASKFLOW - Enterprise Project & Team Collaboration Platform

TASKFLOW is a production-ready Django and Django REST Framework project management platform inspired by Jira, Trello, and Asana. It demonstrates authentication, role-based access, normalized relational modeling, REST APIs, dashboards, Kanban workflows, collaboration, notifications, file uploads, tests, and Docker deployment readiness.

## Features

- JWT authentication with access and refresh tokens using SimpleJWT
- User registration, login, logout, password reset, password change, and profile management
- Roles: Admin, Project Manager, Team Member
- Dashboard with project/task KPIs, overdue tracking, activity feed, Chart.js analytics, and productivity metrics
- Project CRUD with team assignment, dates, status, and progress tracking
- Task CRUD with assignees, priority, workflow status, due dates, tags, and subtasks
- Kanban board with drag-and-drop status updates
- Comments, mentions-ready schema, discussions, activity timeline, and in-app notifications
- SMTP email notifications for assignment, comments, completion, and status changes
- Attachment upload/download with file type and size validation
- Search, filtering, ordering, pagination, and validation across REST APIs
- Admin configuration, unit tests, API tests, Docker, Render deployment config, and environment-driven settings

## Tech Stack

Python, Django, Django REST Framework, SimpleJWT, SQLite, django-filter, Bootstrap 5, Chart.js, JavaScript, SMTP email, Docker, WhiteNoise, Gunicorn.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## API Documentation

Authentication:

- `POST /api/auth/token/` - obtain JWT access and refresh tokens
- `POST /api/auth/token/refresh/` - refresh access token
- `POST /api/accounts/register/` - create user
- `GET/PATCH /api/accounts/me/` - current user profile
- `POST /api/accounts/change-password/` - change password

Project management:

- `/api/projects/` - CRUD, search, filter, ordering, pagination
- `/api/tasks/` - CRUD and task workflow
- `/api/tasks/{id}/move/` - move a task between workflow states
- `/api/comments/` - task comments
- `/api/attachments/` - task attachments
- `/api/discussions/` - project discussions
- `/api/notifications/` - user notifications
- `/api/activity/` - activity timeline
- `/api/dashboard/metrics/` - dashboard analytics payload

All business APIs are JWT protected. Send `Authorization: Bearer <access_token>`.

## Database Design

TASKFLOW uses a normalized relational schema:

- `User` stores Django authentication data.
- `Profile` extends each user with role, title, department, avatar, and bio.
- `Project` stores portfolio metadata and owns tasks, discussions, and activity logs.
- `Project.members` is a many-to-many relationship that models team assignment.
- `Task` belongs to a project, can have a parent task for subtasks, and tracks assignee, reporter, priority, status, due date, tags, and completion time.
- `Comment` belongs to a task and supports many-to-many user mentions.
- `Attachment` belongs to a task and validates upload size and extension.
- `Notification` stores in-app user notifications and read state.
- `ActivityLog` records auditable events across projects and tasks.

## System Architecture

TASKFLOW follows a layered Django architecture:

1. `taskflow.settings` centralizes environment-driven production configuration.
2. `accounts` owns registration, profile management, authentication serializers, and user APIs.
3. `projects` owns domain models, permissions, services, API viewsets, dashboard metrics, and Kanban views.
4. DRF routers expose REST resources with JWT authentication, filtering, search, ordering, and pagination.
5. Bootstrap templates provide a recruiter-friendly SaaS interface for dashboards, profiles, project lists, and Kanban.
6. Service functions isolate cross-cutting notification, email, and activity logging behavior.

## Docker

```bash
copy .env.example .env
docker compose up --build
```

The container runs migrations and serves Django through Gunicorn.

## Render Deployment

1. Push the repository to GitHub.
2. Create a new Render Web Service from the repository.
3. Use the included `render.yaml` or Docker environment.
4. Set `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, SMTP variables, and `SECRET_KEY`.
5. Run `python manage.py migrate` from the Render shell after first deploy if needed.

## Testing

```bash
python manage.py test
```

Included tests cover profile creation, JWT login, authenticated task creation, Kanban workflow moves, and progress recalculation.

