"""
Tests for Kanban Board API endpoints.
"""
import pytest

from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from kanban_app.models import Board, Comment, Task


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def create_user():
    """Create a test user with profile."""
    def _create(email='test@test.de', password='test1234', fullname='Test'):
        user = User.objects.create_user(
            username=email, email=email, password=password
        )
        user.profile.fullname = fullname
        user.profile.save()
        Token.objects.get_or_create(user=user)
        return user
    return _create


@pytest.fixture
def auth_client(api_client, create_user):
    """Return authenticated API client."""
    user = create_user()
    token = Token.objects.get(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client, user


@pytest.mark.django_db
class TestBoardEndpoints:
    """Tests for Board CRUD endpoints."""

    def test_create_board(self, auth_client):
        """Test creating a board."""
        client, user = auth_client
        data = {'title': 'Test Board', 'members': []}
        response = client.post('/api/boards/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['owner_id'] == user.id

    def test_create_board_with_members(self, auth_client, create_user):
        """Test creating a board with members."""
        client, owner = auth_client
        member = create_user(email='member@test.de')
        data = {'title': 'Team Board', 'members': [member.id]}
        response = client.post('/api/boards/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_boards(self, auth_client):
        """Test listing boards."""
        client, user = auth_client
        Board.objects.create(title='My Board', owner=user)
        response = client.get('/api/boards/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_retrieve_board(self, auth_client):
        """Test retrieving a board."""
        client, user = auth_client
        board = Board.objects.create(title='My Board', owner=user)
        response = client.get(f'/api/boards/{board.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_board(self, auth_client):
        """Test updating a board."""
        client, user = auth_client
        board = Board.objects.create(title='Old Title', owner=user)
        response = client.patch(f'/api/boards/{board.id}/', {'title': 'New'})
        assert response.status_code == status.HTTP_200_OK

    def test_delete_board(self, auth_client):
        """Test deleting a board."""
        client, user = auth_client
        board = Board.objects.create(title='To Delete', owner=user)
        response = client.delete(f'/api/boards/{board.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_member_can_access_board(self, api_client, create_user):
        """Test member can access board."""
        owner = create_user(email='owner@test.de')
        member = create_user(email='member@test.de')
        board = Board.objects.create(title='Shared', owner=owner)
        board.members.add(member)
        token = Token.objects.get(user=member)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.get(f'/api/boards/{board.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_non_member_cannot_access(self, api_client, create_user):
        """Test non-member cannot access board."""
        owner = create_user(email='owner@test.de')
        other = create_user(email='other@test.de')
        board = Board.objects.create(title='Private', owner=owner)
        token = Token.objects.get(user=other)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.get(f'/api/boards/{board.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_only_owner_can_delete(self, api_client, create_user):
        """Test only owner can delete board."""
        owner = create_user(email='owner@test.de')
        member = create_user(email='member@test.de')
        board = Board.objects.create(title='Board', owner=owner)
        board.members.add(member)
        token = Token.objects.get(user=member)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.delete(f'/api/boards/{board.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskEndpoints:
    """Tests for Task CRUD endpoints."""

    def test_create_task(self, auth_client):
        """Test creating a task."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        data = {
            'title': 'Test Task',
            'board': board.id,
            'status': 'to-do',
            'priority': 'high'
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_with_assignee(self, auth_client):
        """Test creating a task with assignee."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        data = {
            'title': 'Task',
            'board': board.id,
            'status': 'to-do',
            'priority': 'medium',
            'assignee_id': user.id
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_task(self, auth_client):
        """Test updating a task."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Old', board=board, created_by=user
        )
        response = client.patch(f'/api/tasks/{task.id}/', {'title': 'New'})
        assert response.status_code == status.HTTP_200_OK

    def test_delete_task(self, auth_client):
        """Test deleting a task."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        response = client.delete(f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestAssignedTasks:
    """Tests for assigned tasks endpoint."""

    def test_get_assigned_tasks(self, auth_client):
        """Test getting assigned tasks."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        Task.objects.create(
            title='Assigned', board=board, created_by=user, assignee=user
        )
        Task.objects.create(
            title='Not Assigned', board=board, created_by=user
        )
        response = client.get('/api/tasks/assigned-to-me/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestReviewTasks:
    """Tests for review tasks endpoint."""

    def test_get_review_tasks(self, auth_client):
        """Test getting review tasks."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        Task.objects.create(
            title='For Review', board=board, created_by=user, reviewer=user
        )
        Task.objects.create(
            title='Not Review', board=board, created_by=user
        )
        response = client.get('/api/tasks/reviewing/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestCommentEndpoints:
    """Tests for Comment endpoints."""

    def test_create_comment(self, auth_client):
        """Test creating a comment."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        data = {'content': 'Test comment'}
        response = client.post(
            f'/api/tasks/{task.id}/comments/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_comments(self, auth_client):
        """Test listing comments."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        Comment.objects.create(task=task, author=user, content='Test')
        response = client.get(f'/api/tasks/{task.id}/comments/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_delete_comment(self, auth_client):
        """Test deleting a comment."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        comment = Comment.objects.create(
            task=task, author=user, content='Test'
        )
        response = client.delete(
            f'/api/tasks/{task.id}/comments/{comment.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_comment_nonexistent_task(self, auth_client):
        """Test comment on nonexistent task."""
        client, user = auth_client
        response = client.post(
            '/api/tasks/99999/comments/', {'content': 'Test'}, format='json'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_comments_nonexistent_task(self, auth_client):
        """Test list comments on nonexistent task."""
        client, user = auth_client
        response = client.get('/api/tasks/99999/comments/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_author_cannot_delete_comment(self, api_client, create_user):
        """Test non-author cannot delete comment."""
        owner = create_user(email='owner@test.de')
        other = create_user(email='other@test.de')
        board = Board.objects.create(title='Board', owner=owner)
        board.members.add(other)
        task = Task.objects.create(title='Task', board=board, created_by=owner)
        comment = Comment.objects.create(task=task, author=owner, content='T')
        token = Token.objects.get(user=other)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = f'/api/tasks/{task.id}/comments/{comment.id}/'
        assert api_client.delete(url).status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEdgeCases:
    """Tests for edge cases."""

    def test_create_task_nonexistent_board(self, auth_client):
        """Test creating task on nonexistent board."""
        client, user = auth_client
        data = {
            'title': 'Task',
            'board': 99999,
            'status': 'to-do',
            'priority': 'medium'
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_invalid_assignee(self, auth_client, create_user):
        """Test updating task with invalid assignee."""
        client, user = auth_client
        other = create_user(email='other@test.de')
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/', {'assignee_id': other.id}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_task_invalid_reviewer(self, auth_client, create_user):
        """Test updating task with invalid reviewer."""
        client, user = auth_client
        other = create_user(email='other@test.de')
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/', {'reviewer_id': other.id}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_member_cannot_delete_others_task(self, api_client, create_user):
        """Test member cannot delete others task."""
        owner = create_user(email='owner@test.de')
        member = create_user(email='member@test.de')
        board = Board.objects.create(title='Board', owner=owner)
        board.members.add(member)
        task = Task.objects.create(
            title='Task', board=board, created_by=owner
        )
        token = Token.objects.get(user=member)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.delete(f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_board_owner_can_delete_task(self, api_client, create_user):
        """Test board owner can delete any task."""
        owner = create_user(email='owner@test.de')
        member = create_user(email='member@test.de')
        board = Board.objects.create(title='Board', owner=owner)
        board.members.add(member)
        task = Task.objects.create(
            title='Task', board=board, created_by=member
        )
        token = Token.objects.get(user=owner)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.delete(f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_member_cannot_comment(self, api_client, create_user):
        """Test non-member cannot comment."""
        owner = create_user(email='owner@test.de')
        other = create_user(email='other@test.de')
        board = Board.objects.create(title='Board', owner=owner)
        task = Task.objects.create(
            title='Task', board=board, created_by=owner
        )
        token = Token.objects.get(user=other)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = api_client.post(
            f'/api/tasks/{task.id}/comments/',
            {'content': 'Test'},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_with_reviewer(self, auth_client):
        """Test creating task with reviewer."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        data = {
            'title': 'Task',
            'board': board.id,
            'status': 'to-do',
            'priority': 'medium',
            'reviewer_id': user.id
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_task_null_assignee(self, auth_client):
        """Test updating task with null assignee."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user, assignee=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/',
            {'assignee_id': None},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_task_null_reviewer(self, auth_client):
        """Test updating task with null reviewer."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user, reviewer=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/',
            {'reviewer_id': None},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_validate_null_assignee(self, auth_client):
        """Test validation passes for null assignee."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        data = {
            'title': 'Task',
            'board': board.id,
            'status': 'to-do',
            'priority': 'medium',
            'assignee_id': None
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_validate_null_reviewer(self, auth_client):
        """Test validation passes for null reviewer."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        data = {
            'title': 'Task',
            'board': board.id,
            'status': 'to-do',
            'priority': 'medium',
            'reviewer_id': None
        }
        response = client.post('/api/tasks/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_board_with_members(self, auth_client, create_user):
        """Test updating board with members."""
        client, user = auth_client
        member = create_user(email='member@test.de')
        board = Board.objects.create(title='Board', owner=user)
        response = client.patch(
            f'/api/boards/{board.id}/',
            {'members': [member.id]},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSerializerEdgeCases:
    """Tests for serializer edge cases."""

    def test_update_task_set_assignee(self, auth_client):
        """Test setting assignee on update."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/',
            {'assignee_id': user.id},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.assignee_id == user.id

    def test_update_task_set_reviewer(self, auth_client):
        """Test setting reviewer on update."""
        client, user = auth_client
        board = Board.objects.create(title='Board', owner=user)
        task = Task.objects.create(
            title='Task', board=board, created_by=user
        )
        response = client.patch(
            f'/api/tasks/{task.id}/',
            {'reviewer_id': user.id},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.reviewer_id == user.id
