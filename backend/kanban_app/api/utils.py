"""
Utility functions for Kanban Board API.
"""
from rest_framework import status
from rest_framework.response import Response

from ..models import Board, Task


def get_user_boards(user):
    """Return boards where user is owner or member."""
    owned = Board.objects.filter(owner=user)
    member = Board.objects.filter(members=user)
    return (owned | member).distinct()


def check_task_access(task_id, user):
    """Check if user can access task and return task or error response."""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return None, Response(
            {'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND
        )

    if task.board not in get_user_boards(user):
        return None, Response(
            {'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN
        )

    return task, None
