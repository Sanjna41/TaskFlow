from django.urls import include, path
from rest_framework.routers import DefaultRouter

from projects import views

router = DefaultRouter()
router.register("projects", views.ProjectViewSet, basename="project")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("comments", views.CommentViewSet, basename="comment")
router.register("attachments", views.AttachmentViewSet, basename="attachment")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("activity", views.ActivityLogViewSet, basename="activity")
router.register("discussions", views.ProjectDiscussionViewSet, basename="discussion")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/metrics/", views.dashboard_metrics, name="api_dashboard_metrics"),
]
