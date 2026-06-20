from rest_framework import permissions


def role_for(user):
    return getattr(getattr(user, "profile", None), "role", "team_member")


class IsAdminOrProjectManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or role_for(request.user) in {"admin", "project_manager"})


class ProjectMembershipPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        project = getattr(obj, "project", obj)
        if user.is_staff or role_for(user) == "admin":
            return True
        return project.manager_id == user.id or project.members.filter(id=user.id).exists()
