"""
Tests for authentication endpoints.
"""
import pytest

from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


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
class TestRegistration:
    """Tests for registration endpoint."""

    def test_registration_success(self, api_client):
        """Test successful registration."""
        data = {
            'fullname': 'Max Mustermann',
            'email': 'new@test.de',
            'password': 'test1234',
            'repeated_password': 'test1234'
        }
        response = api_client.post('/api/registration/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data

    def test_registration_duplicate_email(self, api_client, create_user):
        """Test registration with duplicate email."""
        create_user(email='existing@test.de')
        data = {
            'fullname': 'New User',
            'email': 'existing@test.de',
            'password': 'test1234',
            'repeated_password': 'test1234'
        }
        response = api_client.post('/api/registration/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_password_mismatch(self, api_client):
        """Test registration with password mismatch."""
        data = {
            'fullname': 'New User',
            'email': 'new@test.de',
            'password': 'test1234',
            'repeated_password': 'different'
        }
        response = api_client.post('/api/registration/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_short_password(self, api_client):
        """Test registration with short password."""
        data = {
            'fullname': 'New User',
            'email': 'new@test.de',
            'password': '123',
            'repeated_password': '123'
        }
        response = api_client.post('/api/registration/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_missing_fields(self, api_client):
        """Test registration with missing fields."""
        response = api_client.post('/api/registration/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, api_client, create_user):
        """Test successful login."""
        create_user(email='login@test.de', password='test1234')
        data = {'email': 'login@test.de', 'password': 'test1234'}
        response = api_client.post('/api/login/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data

    def test_login_wrong_password(self, api_client, create_user):
        """Test login with wrong password."""
        create_user(email='login@test.de', password='test1234')
        data = {'email': 'login@test.de', 'password': 'wrong'}
        response = api_client.post('/api/login/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login with nonexistent user."""
        data = {'email': 'nonexistent@test.de', 'password': 'test1234'}
        response = api_client.post('/api/login/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_fields(self, api_client):
        """Test login with missing fields."""
        response = api_client.post('/api/login/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEmailCheck:
    """Tests for email check endpoint."""

    def test_email_check_found(self, auth_client, create_user):
        """Test email check when found."""
        client, _ = auth_client
        create_user(email='found@test.de', fullname='Found')
        response = client.get('/api/email-check/?email=found@test.de')
        assert response.status_code == status.HTTP_200_OK

    def test_email_check_not_found(self, auth_client):
        """Test email check when not found."""
        client, _ = auth_client
        response = client.get('/api/email-check/?email=notfound@test.de')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_email_check_missing_param(self, auth_client):
        """Test email check without param."""
        client, _ = auth_client
        response = client.get('/api/email-check/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_check_unauthenticated(self, api_client):
        """Test email check requires auth."""
        response = api_client.get('/api/email-check/?email=test@test.de')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
