from django.conf import settings
from django.core.mail import send_mail

from projects.models import ActivityLog, Notification


def record_activity(actor, verb, detail="", project=None, task=None):
    return ActivityLog.objects.create(actor=actor, verb=verb, detail=detail, project=project, task=task)


def notify_user(recipient, kind, message, actor=None, task=None, email_subject=None):
    notification = Notification.objects.create(recipient=recipient, actor=actor, task=task, kind=kind, message=message)
    if recipient.email:
        send_mail(email_subject or "TaskFlow notification", message, settings.DEFAULT_FROM_EMAIL, [recipient.email], fail_silently=True)
    return notification
