"""
URL routes for Kanban Board API.
"""
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    AssignedTasksView, BoardViewSet, CommentViewSet,
    ReviewTasksView, TaskViewSet
)

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path(
        'tasks/assigned-to-me/',
        AssignedTasksView.as_view(),
        name='assigned-tasks'
    ),
    path(
        'tasks/reviewing/',
        ReviewTasksView.as_view(),
        name='review-tasks'
    ),
    path(
        'tasks/<int:task_id>/comments/',
        CommentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='task-comments'
    ),
    path(
        'tasks/<int:task_id>/comments/<int:pk>/',
        CommentViewSet.as_view({'delete': 'destroy'}),
        name='task-comment-detail'
    ),
    path('', include(router.urls)),
]
