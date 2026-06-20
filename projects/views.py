from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, permissions, response, viewsets

from projects.models import ActivityLog, Attachment, Comment, Notification, Project, ProjectDiscussion, Task
from projects.permissions import IsAdminOrProjectManager, ProjectMembershipPermission
from projects.serializers import (
    ActivityLogSerializer,
    AttachmentSerializer,
    CommentSerializer,
    NotificationSerializer,
    ProjectDiscussionSerializer,
    ProjectSerializer,
    TaskSerializer,
)
from projects.services import notify_user, record_activity


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectMembershipPermission]
    filterset_fields = ["status", "manager", "members"]
    search_fields = ["name", "key", "description"]
    ordering_fields = ["start_date", "end_date", "progress", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Project.objects.select_related("manager").prefetch_related("members")
        if user.is_staff or getattr(user.profile, "role", "") == "admin":
            return qs
        return qs.filter(Q(manager=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        project = serializer.save()
        project.members.add(project.manager)
        record_activity(self.request.user, "created project", project=project, detail=project.name)

    def get_permissions(self):
        if self.action in {"create", "destroy"}:
            return [permissions.IsAuthenticated(), IsAdminOrProjectManager()]
        return super().get_permissions()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectMembershipPermission]
    filterset_fields = ["project", "status", "priority", "assignee", "due_date"]
    search_fields = ["title", "description", "tags"]
    ordering_fields = ["due_date", "priority", "status", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related("project", "assignee", "reporter").prefetch_related("comments", "attachments")
        if user.is_staff or getattr(user.profile, "role", "") == "admin":
            return qs
        return qs.filter(Q(project__manager=user) | Q(project__members=user) | Q(assignee=user)).distinct()

    def perform_create(self, serializer):
        task = serializer.save(reporter=self.request.user)
        record_activity(self.request.user, "created task", project=task.project, task=task, detail=task.title)
        if task.assignee:
            notify_user(task.assignee, Notification.Kind.TASK_ASSIGNED, f"You were assigned: {task.title}", self.request.user, task, "New TaskFlow assignment")

    def perform_update(self, serializer):
        previous = self.get_object()
        task = serializer.save()
        kind = Notification.Kind.TASK_COMPLETED if task.status == Task.Status.COMPLETED else Notification.Kind.TASK_UPDATED
        record_activity(self.request.user, "updated task", project=task.project, task=task, detail=task.title)
        if task.assignee and previous.status != task.status:
            notify_user(task.assignee, kind, f"{task.title} moved to {task.get_status_display()}", self.request.user, task, "TaskFlow task status changed")

    @decorators.action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(task, data={"status": request.data.get("status")}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_activity(request.user, "moved task", project=task.project, task=task, detail=task.get_status_display())
        return response.Response(self.get_serializer(task).data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectMembershipPermission]
    filterset_fields = ["task", "author"]
    search_fields = ["body"]

    def get_queryset(self):
        return Comment.objects.select_related("task", "author", "task__project")

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        record_activity(self.request.user, "commented", project=comment.task.project, task=comment.task, detail=comment.body[:120])
        if comment.task.assignee and comment.task.assignee != self.request.user:
            notify_user(comment.task.assignee, Notification.Kind.NEW_COMMENT, f"New comment on {comment.task.title}", self.request.user, comment.task, "TaskFlow comment alert")


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectMembershipPermission]
    filterset_fields = ["task", "uploaded_by"]

    def get_queryset(self):
        return Attachment.objects.select_related("task", "uploaded_by", "task__project")

    def perform_create(self, serializer):
        uploaded = self.request.FILES.get("file")
        serializer.save(uploaded_by=self.request.user, original_name=uploaded.name if uploaded else "")


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("actor", "task")

    @decorators.action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return response.Response({"detail": "Notification marked as read."})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    filterset_fields = ["project", "task", "actor"]

    def get_queryset(self):
        return ActivityLog.objects.select_related("actor", "project", "task")[:100]


class ProjectDiscussionViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectDiscussionSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectMembershipPermission]
    filterset_fields = ["project", "author"]
    search_fields = ["topic", "body"]

    def get_queryset(self):
        return ProjectDiscussion.objects.select_related("project", "author")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def dashboard_metrics(request):
    user = request.user
    projects = Project.objects.all() if user.is_staff else Project.objects.filter(Q(manager=user) | Q(members=user)).distinct()
    tasks = Task.objects.filter(project__in=projects)
    return response.Response(
        {
            "total_projects": projects.count(),
            "total_tasks": tasks.count(),
            "completed_tasks": tasks.filter(status=Task.Status.COMPLETED).count(),
            "pending_tasks": tasks.exclude(status=Task.Status.COMPLETED).count(),
            "overdue_tasks": tasks.filter(due_date__lt=timezone.localdate()).exclude(status=Task.Status.COMPLETED).count(),
            "by_status": list(tasks.values("status").annotate(total=Count("id"))),
            "by_priority": list(tasks.values("priority").annotate(total=Count("id"))),
        }
    )


@login_required
def dashboard(request):
    projects = Project.objects.filter(Q(manager=request.user) | Q(members=request.user)).distinct()
    tasks = Task.objects.filter(project__in=projects)
    context = {
        "projects": projects[:6],
        "recent_activity": ActivityLog.objects.select_related("actor", "project", "task")[:12],
        "total_projects": projects.count(),
        "total_tasks": tasks.count(),
        "completed_tasks": tasks.filter(status=Task.Status.COMPLETED).count(),
        "pending_tasks": tasks.exclude(status=Task.Status.COMPLETED).count(),
        "overdue_tasks": tasks.filter(due_date__lt=timezone.localdate()).exclude(status=Task.Status.COMPLETED).count(),
        "team_metrics": tasks.values("assignee__username").annotate(total=Count("id"), completed=Count("id", filter=Q(status=Task.Status.COMPLETED)))[:8],
    }
    return render(request, "dashboard.html", context)


@login_required
def project_list(request):
    projects = Project.objects.filter(Q(manager=request.user) | Q(members=request.user)).distinct()
    query = request.GET.get("q")
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(key__icontains=query) | Q(description__icontains=query))
    return render(request, "projects/project_list.html", {"projects": projects})


@login_required
def kanban_board(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    columns = {status: project.tasks.filter(status=status).select_related("assignee") for status, _ in Task.Status.choices}
    return render(request, "projects/kanban.html", {"project": project, "columns": columns, "statuses": Task.Status.choices})


@login_required
@require_POST
def move_task_web(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.status = request.POST.get("status", task.status)
    task.save(update_fields=["status", "completed_at", "updated_at"])
    record_activity(request.user, "moved task", project=task.project, task=task, detail=task.get_status_display())
    return redirect("kanban", project_id=task.project_id)
