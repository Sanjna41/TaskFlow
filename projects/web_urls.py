from django.urls import path

from projects import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("<int:project_id>/kanban/", views.kanban_board, name="kanban"),
    path("tasks/<int:task_id>/move/", views.move_task_web, name="move_task_web"),
]
