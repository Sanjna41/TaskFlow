from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.forms import ProfileForm, RegistrationForm
from accounts.serializers import ChangePasswordSerializer, RegisterSerializer, UserSerializer


class TaskFlowLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class TaskFlowLogoutView(LogoutView):
    next_page = reverse_lazy("login")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to TaskFlow. Your workspace is ready.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user.profile)
    password_form = PasswordChangeForm(request.user)
    return render(request, "accounts/profile.html", {"form": form, "password_form": password_form})


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
