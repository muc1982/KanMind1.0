"""
Tests for models.
"""
import pytest

from django.contrib.auth.models import User

from auth_app.models import UserProfile
from kanban_app.models import Board, Comment, Task


@pytest.fixture
def create_user():
    """Create a test user with profile."""
    def _create(email='test@test.de', fullname='Test User'):
        user = User.objects.create_user(
            username=email, email=email, password='test1234'
        )
        user.profile.fullname = fullname
        user.profile.save()
        return user
    return _create


@pytest.mark.django_db
class TestUserProfile:
    """Tests for UserProfile model."""

    def test_profile_created_on_user_creation(self):
        """Test profile is auto-created."""
        user = User.objects.create_user(
            username='test@test.de', email='test@test.de', password='test1234'
        )
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)

    def test_profile_str(self, create_user):
        """Test profile string representation."""
        user = create_user(fullname='Max Mustermann')
        assert str(user.profile) == 'Max Mustermann'


@pytest.mark.django_db
class TestBoardModel:
    """Tests for Board model."""

    def test_board_str(self, create_user):
        """Test board string representation."""
        user = create_user()
        board = Board.objects.create(title='Test Board', owner=user)
        assert str(board) == 'Test Board'

    def test_board_ordering(self, create_user):
        """Test boards are ordered by created_at descending."""
        user = create_user()
        Board.objects.create(title='First', owner=user)
        Board.objects.create(title='Second', owner=user)
        boards = Board.objects.all()
        assert boards[0].title == 'Second'
        assert boards[1].title == 'First'


@pytest.mark.django_db
class TestTaskModel:
    """Tests for Task model."""

    def test_task_str(self, create_user):
        """Test task string representation."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Test Task', board=board, created_by=user
        )
        assert str(task) == 'Test Task'

    def test_task_default_status(self, create_user):
        """Test task default status is to-do."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        assert task.status == 'to-do'

    def test_task_default_priority(self, create_user):
        """Test task default priority is medium."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        assert task.priority == 'medium'

    def test_task_ordering(self, create_user):
        """Test tasks are ordered by created_at ascending."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        Task.objects.create(title='First', board=board, created_by=user)
        Task.objects.create(title='Second', board=board, created_by=user)
        tasks = Task.objects.all()
        assert tasks[0].title == 'First'


@pytest.mark.django_db
class TestCommentModel:
    """Tests for Comment model."""

    def test_comment_str(self, create_user):
        """Test comment string representation."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        comment = Comment.objects.create(
            task=task, author=user, content='Test'
        )
        assert 'Comment by' in str(comment)

    def test_comment_ordering(self, create_user):
        """Test comments are ordered by created_at ascending."""
        user = create_user()
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        Comment.objects.create(task=task, author=user, content='First')
        Comment.objects.create(task=task, author=user, content='Second')
        comments = Comment.objects.all()
        assert comments[0].content == 'First'
