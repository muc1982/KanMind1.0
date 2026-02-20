"""
Views for Kanban Board API.
"""
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Board, Comment, Task
from .permissions import (
    IsBoardMember, IsBoardOwner,
    IsCommentAuthor, IsTaskOwnerOrBoardOwner
)
from .serializers import (
    BoardCreateSerializer, BoardDetailSerializer,
    BoardListSerializer, BoardUpdateSerializer,
    CommentSerializer, TaskListSerializer, TaskSerializer
)
from .utils import check_task_access, get_user_boards


class BoardViewSet(viewsets.ModelViewSet):
    """ViewSet for Board CRUD operations."""
    permission_classes = [IsAuthenticated]
    serializer_class = BoardListSerializer
    queryset = Board.objects.all()

    def get_queryset(self):
        """Return boards where user is owner or member."""
        if self.action == 'list':
            return get_user_boards(self.request.user)
        return Board.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        serializer_map = {
            'list': BoardListSerializer,
            'retrieve': BoardDetailSerializer,
            'create': BoardCreateSerializer,
            'update': BoardUpdateSerializer,
            'partial_update': BoardUpdateSerializer,
        }
        return serializer_map.get(self.action, BoardListSerializer)

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action == 'destroy':
            return [IsAuthenticated(), IsBoardOwner()]
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated(), IsBoardMember()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Set the owner to the current user."""
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create board and return list format response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_data = BoardListSerializer(serializer.instance).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task CRUD operations."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]
    http_method_names = ['post', 'patch', 'delete']
    queryset = Task.objects.all()

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action == 'destroy':
            return [IsAuthenticated(), IsTaskOwnerOrBoardOwner()]
        return [IsAuthenticated(), IsBoardMember()]

    def perform_create(self, serializer):
        """Set the created_by to the current user."""
        serializer.save(created_by=self.request.user)


class AssignedTasksView(APIView):
    """View for tasks assigned to current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all tasks assigned to current user."""
        tasks = Task.objects.filter(assignee=request.user)
        return Response(TaskListSerializer(tasks, many=True).data)


class ReviewTasksView(APIView):
    """View for tasks where current user is reviewer."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all tasks where current user is reviewer."""
        tasks = Task.objects.filter(reviewer=request.user)
        return Response(TaskListSerializer(tasks, many=True).data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment CRUD operations."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments for specific task."""
        return Comment.objects.filter(task_id=self.kwargs.get('task_id'))

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action == 'destroy':
            return [IsAuthenticated(), IsCommentAuthor()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create comment for task."""
        task_id = self.kwargs.get('task_id')
        task, error = check_task_access(task_id, request.user)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List comments - check board membership."""
        task_id = self.kwargs.get('task_id')
        task, error = check_task_access(task_id, request.user)
        if error:
            return error
        return super().list(request, *args, **kwargs)
