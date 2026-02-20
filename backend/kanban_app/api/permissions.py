"""
Custom permissions for Kanban Board API.
"""
from rest_framework import permissions
from rest_framework.exceptions import NotFound

from ..models import Board


class IsBoardOwner(permissions.BasePermission):
    """Permission to check if user is board owner."""

    def has_object_permission(self, request, view, obj):
        """Check if user owns the board."""
        return obj.owner == request.user


class IsBoardMember(permissions.BasePermission):
    """Permission to check if user is board member or owner."""

    def has_permission(self, request, view):
        """Check board membership for create actions."""
        if view.action == 'create':
            board_id = request.data.get('board')
            if not board_id:
                return False
            try:
                board = Board.objects.get(id=board_id)
            except Board.DoesNotExist:
                raise NotFound(detail='Board not found.')
            return self.is_member_or_owner(request.user, board)
        return True

    def has_object_permission(self, request, view, obj):
        """Check if user is member or owner of the board."""
        board = obj if isinstance(obj, Board) else obj.board
        return self.is_member_or_owner(request.user, board)

    def is_member_or_owner(self, user, board):
        """Check if user is member or owner."""
        return board.owner == user or board.members.filter(id=user.id).exists()


class IsTaskOwnerOrBoardOwner(permissions.BasePermission):
    """Permission to check if user is task creator or board owner."""

    def has_object_permission(self, request, view, obj):
        """Check if user created the task or owns the board."""
        board = obj.board
        is_member = (
            board.owner == request.user
            or board.members.filter(id=request.user.id).exists()
        )
        if not is_member:
            return False
        return obj.created_by == request.user or board.owner == request.user


class IsCommentAuthor(permissions.BasePermission):
    """Permission to check if user is comment author."""

    def has_object_permission(self, request, view, obj):
        """Check if user is the comment author."""
        return obj.author == request.user
