"""
Admin configuration for Auth App.
"""
from django.contrib import admin

from auth_app.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ['user', 'fullname']
    search_fields = ['user__email', 'fullname']
