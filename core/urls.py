from django.urls import path

from projects.views import dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
]
