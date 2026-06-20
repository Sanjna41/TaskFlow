from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class AuthenticationTests(TestCase):
    def test_registration_creates_profile(self):
        user = User.objects.create_user(username="ana", email="ana@example.com", password="StrongPass123!")
        self.assertEqual(user.profile.role, "team_member")

    def test_jwt_login_returns_tokens(self):
        User.objects.create_user(username="sam", password="StrongPass123!")
        response = APIClient().post("/api/auth/token/", {"username": "sam", "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
