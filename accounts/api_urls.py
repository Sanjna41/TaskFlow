from django.urls import path

from accounts.views import ChangePasswordAPIView, MeAPIView, RegisterAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("me/", MeAPIView.as_view(), name="api_me"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="api_change_password"),
]
