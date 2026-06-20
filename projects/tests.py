from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Profile
from projects.models import Project, Task


class ProjectAPITests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user("pm", password="StrongPass123!")
        self.manager.profile.role = Profile.Role.PROJECT_MANAGER
        self.manager.profile.save()
        self.member = User.objects.create_user("dev", password="StrongPass123!")
        self.project = Project.objects.create(
            name="Recruiter Demo",
            key="RD",
            manager=self.manager,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
        )
        self.project.members.add(self.member)
        self.client = APIClient()
        token = self.client.post("/api/auth/token/", {"username": "pm", "password": "StrongPass123!"}, format="json").data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_task_crud_and_project_progress(self):
        response = self.client.post(
            "/api/tasks/",
            {"project": self.project.id, "title": "Build dashboard", "assignee": self.member.id, "priority": "high", "status": "todo"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        task_id = response.data["id"]
        response = self.client.post(f"/api/tasks/{task_id}/move/", {"status": Task.Status.COMPLETED}, format="json")
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.progress, 100)
