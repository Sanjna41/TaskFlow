from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    path("login/", views.TaskFlowLoginView.as_view(), name="login"),
    path("logout/", views.TaskFlowLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("change-password/", auth_views.PasswordChangeView.as_view(template_name="registration/change_password.html", success_url="/accounts/profile/"), name="change_password"),
]
