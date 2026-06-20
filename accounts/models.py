from django.conf import settings
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        PROJECT_MANAGER = "project_manager", "Project Manager"
        TEAM_MEMBER = "team_member", "Team Member"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.TEAM_MEMBER)
    job_title = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
