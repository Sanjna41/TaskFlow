from django.contrib import admin

from projects.models import ActivityLog, Attachment, Comment, Notification, Project, ProjectDiscussion, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "status", "manager", "progress", "start_date", "end_date")
    list_filter = ("status", "manager")
    search_fields = ("name", "key", "description")
    filter_horizontal = ("members",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assignee", "priority", "status", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "tags")


admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(Notification)
admin.site.register(ActivityLog)
admin.site.register(ProjectDiscussion)
