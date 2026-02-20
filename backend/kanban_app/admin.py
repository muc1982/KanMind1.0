"""
Admin configuration for Kanban Board.
"""
from django.contrib import admin

from .models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin for Board model."""
    list_display = ['title', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    filter_horizontal = ['members']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin for Task model."""
    list_display = [
        'title', 'status', 'priority', 'board',
        'assignee', 'reviewer', 'created_at'
    ]
    list_filter = ['status', 'priority', 'board', 'assignee']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for Comment model."""
    list_display = ['task', 'author', 'created_at']
    list_filter = ['task', 'author']
