from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_attachment(file):
    max_size = 10 * 1024 * 1024
    allowed = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".txt", ".csv", ".xlsx", ".zip"}
    suffix = file.name[file.name.rfind(".") :].lower() if "." in file.name else ""
    if file.size > max_size:
        raise ValidationError("Attachment must be 10MB or smaller.")
    if suffix not in allowed:
        raise ValidationError("Unsupported attachment type.")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On Hold"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=180)
    key = models.SlugField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="managed_projects")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="projects", blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.key} - {self.name}"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        if self.progress > 100:
            raise ValidationError("Progress cannot exceed 100%.")

    def recalculate_progress(self):
        total = self.tasks.count()
        completed = self.tasks.filter(status=Task.Status.COMPLETED).count()
        self.progress = round((completed / total) * 100) if total else 0
        self.save(update_fields=["progress", "updated_at"])


class Task(TimeStampedModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        REVIEW = "review", "Review"
        COMPLETED = "completed", "Completed"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="subtasks", blank=True, null=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="assigned_tasks", blank=True, null=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_tasks")
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    due_date = models.DateField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("due_date", "-priority", "-updated_at")
        indexes = [models.Index(fields=["status", "priority"]), models.Index(fields=["due_date"])]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.localdate() and self.status != self.Status.COMPLETED

    def save(self, *args, **kwargs):
        self.completed_at = timezone.now() if self.status == self.Status.COMPLETED and not self.completed_at else self.completed_at
        if self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)
        self.project.recalculate_progress()


class Comment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_comments")
    body = models.TextField()
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="mentions", blank=True)

    class Meta:
        ordering = ("created_at",)


class ProjectDiscussion(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="discussions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.CharField(max_length=180)
    body = models.TextField()

    class Meta:
        ordering = ("-created_at",)


class Attachment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to="task_attachments/%Y/%m/", validators=[validate_attachment])
    original_name = models.CharField(max_length=255)

    def __str__(self):
        return self.original_name


class Notification(TimeStampedModel):
    class Kind(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task Assigned"
        TASK_UPDATED = "task_updated", "Task Updated"
        TASK_COMPLETED = "task_completed", "Task Completed"
        NEW_COMMENT = "new_comment", "New Comment"
        DUE_DATE_REMINDER = "due_date_reminder", "Due Date Reminder"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="sent_notifications")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    kind = models.CharField(max_length=40, choices=Kind.choices)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)


class ActivityLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activity_logs", blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activity_logs", blank=True, null=True)
    verb = models.CharField(max_length=120)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)
