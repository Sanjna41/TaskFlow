from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import Notification, Task
from projects.services import notify_user, record_activity


class Command(BaseCommand):
    help = "Send in-app and email reminders for tasks due within the next day."

    def handle(self, *args, **options):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        tasks = Task.objects.filter(due_date__lte=tomorrow).exclude(status=Task.Status.COMPLETED).select_related("assignee", "project")
        sent = 0
        for task in tasks:
            if not task.assignee:
                continue
            message = f"{task.title} is due on {task.due_date}."
            exists = Notification.objects.filter(
                recipient=task.assignee,
                task=task,
                kind=Notification.Kind.DUE_DATE_REMINDER,
                created_at__date=today,
            ).exists()
            if exists:
                continue
            notify_user(task.assignee, Notification.Kind.DUE_DATE_REMINDER, message, task=task, email_subject="TaskFlow due date reminder")
            record_activity(None, "sent due date reminder", project=task.project, task=task, detail=message)
            sent += 1
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} due date reminder(s)."))
