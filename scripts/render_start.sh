
set -e

python manage.py migrate --noinput

python manage.py shell <<'PY'
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Profile
from projects.models import Comment, Notification, Project, Task


User = get_user_model()
password = "DemoPass123!"
today = timezone.localdate()


def user(username, first_name, last_name, email, role):
    obj, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_active": True,
        },
    )
    obj.first_name = first_name
    obj.last_name = last_name
    obj.email = email
    obj.is_active = True
    obj.set_password(password)
    obj.save()
    profile, _ = Profile.objects.get_or_create(user=obj)
    profile.role = role
    profile.job_title = role.replace("_", " ").title()
    profile.department = "Product Engineering"
    profile.save()
    return obj


pm = user("pm_demo", "Priya", "Sharma", "priya.pm@example.com", Profile.Role.PROJECT_MANAGER)
dev = user("developer_demo", "Rohan", "Verma", "rohan.dev@example.com", Profile.Role.TEAM_MEMBER)
qa = user("qa_demo", "Sara", "Khan", "sara.qa@example.com", Profile.Role.TEAM_MEMBER)

launch, _ = Project.objects.update_or_create(
    key="TFLOW",
    defaults={
        "name": "TaskFlow Launch Workspace",
        "description": "Recruiter-facing project plan for polishing TaskFlow before GitHub and live deployment.",
        "status": Project.Status.ACTIVE,
        "manager": pm,
        "start_date": today - timedelta(days=10),
        "end_date": today + timedelta(days=25),
    },
)
launch.members.set([pm, dev, qa])

mobile, _ = Project.objects.update_or_create(
    key="MOB",
    defaults={
        "name": "Mobile Experience Planning",
        "description": "Responsive UI and future mobile workflow discovery.",
        "status": Project.Status.PLANNING,
        "manager": pm,
        "start_date": today,
        "end_date": today + timedelta(days=45),
    },
)
mobile.members.set([pm, dev, qa])

task_data = [
    (launch, "Finalize GitHub README and setup guide", dev, Task.Priority.HIGH, Task.Status.COMPLETED, -2),
    (launch, "Configure Render production environment", pm, Task.Priority.CRITICAL, Task.Status.IN_PROGRESS, 2),
    (launch, "Validate JWT permission boundaries", qa, Task.Priority.HIGH, Task.Status.REVIEW, 3),
    (launch, "Capture dashboard and Kanban screenshots", dev, Task.Priority.MEDIUM, Task.Status.TODO, 5),
    (launch, "Add API examples for recruiter walkthrough", pm, Task.Priority.MEDIUM, Task.Status.TODO, 6),
    (mobile, "Audit responsive project navigation", qa, Task.Priority.HIGH, Task.Status.IN_PROGRESS, 8),
    (mobile, "Design mobile-friendly task move controls", dev, Task.Priority.MEDIUM, Task.Status.REVIEW, 10),
    (mobile, "Prepare accessibility checklist", qa, Task.Priority.MEDIUM, Task.Status.TODO, 12),
    (mobile, "Document future notification center", pm, Task.Priority.LOW, Task.Status.TODO, 16),
    (mobile, "Review production database migration plan", dev, Task.Priority.CRITICAL, Task.Status.TODO, 18),
]

tasks = []
for project, title, assignee, priority, status, offset in task_data:
    task, _ = Task.objects.update_or_create(
        project=project,
        title=title,
        defaults={
            "description": f"Demo task for recruiter walkthrough: {title.lower()}.",
            "assignee": assignee,
            "reporter": pm,
            "priority": priority,
            "status": status,
            "due_date": today + timedelta(days=offset),
            "tags": "demo, recruiter",
        },
    )
    tasks.append(task)

comments = [
    "This is ready for a recruiter walkthrough once the screenshots are attached.",
    "Please confirm the environment variable names match the Render dashboard.",
    "I checked the happy path; next pass should cover unauthorized users.",
    "Use realistic data in the screenshots so the dashboard tells a clear story.",
    "Add one concise API request example that shows JWT authentication.",
    "Mobile spacing looks good overall, but the Kanban columns need a fallback action.",
    "The review state is a nice talking point for workflow design decisions.",
    "This checklist will help explain how accessibility was considered.",
    "Good roadmap candidate after the deployment demo is stable.",
    "PostgreSQL is the right next step before calling this production-ready.",
]
for task, body in zip(tasks, comments):
    Comment.objects.get_or_create(task=task, author=pm, body=body)

notification_data = [
    (dev, pm, tasks[1], Notification.Kind.TASK_ASSIGNED, "You were assigned: Configure Render production environment"),
    (qa, pm, tasks[2], Notification.Kind.TASK_UPDATED, "JWT permission review moved to Review."),
    (dev, qa, tasks[6], Notification.Kind.NEW_COMMENT, "New QA comment on mobile task controls."),
    (pm, dev, tasks[0], Notification.Kind.TASK_COMPLETED, "README setup guide is complete."),
    (dev, pm, tasks[9], Notification.Kind.DUE_DATE_REMINDER, "Production database migration plan is due soon."),
]
for recipient, actor, task, kind, message in notification_data:
    Notification.objects.get_or_create(
        recipient=recipient,
        actor=actor,
        task=task,
        kind=kind,
        defaults={"message": message},
    )

print("Render demo data ready. Login with pm_demo / DemoPass123!")
PY

gunicorn taskflow.wsgi:application --bind 0.0.0.0:8000