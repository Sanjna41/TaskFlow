from django.contrib import admin

from accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "job_title", "department", "updated_at")
    list_filter = ("role", "department")
    search_fields = ("user__username", "user__email", "job_title", "department")
