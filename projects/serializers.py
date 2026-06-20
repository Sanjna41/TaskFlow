from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import ActivityLog, Attachment, Comment, Notification, Project, ProjectDiscussion, Task

User = get_user_model()


class CompactUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "email")


class ProjectSerializer(serializers.ModelSerializer):
    manager_detail = CompactUserSerializer(source="manager", read_only=True)
    members_detail = CompactUserSerializer(source="members", read_only=True, many=True)

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("progress",)

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    assignee_detail = CompactUserSerializer(source="assignee", read_only=True)
    reporter_detail = CompactUserSerializer(source="reporter", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("reporter", "completed_at")


class CommentSerializer(serializers.ModelSerializer):
    author_detail = CompactUserSerializer(source="author", read_only=True)

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ("author",)


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_detail = CompactUserSerializer(source="uploaded_by", read_only=True)

    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("uploaded_by", "original_name")


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ("recipient", "actor", "task", "kind", "message")


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_detail = CompactUserSerializer(source="actor", read_only=True)

    class Meta:
        model = ActivityLog
        fields = "__all__"


class ProjectDiscussionSerializer(serializers.ModelSerializer):
    author_detail = CompactUserSerializer(source="author", read_only=True)

    class Meta:
        model = ProjectDiscussion
        fields = "__all__"
        read_only_fields = ("author",)
