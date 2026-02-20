"""
Views for authentication endpoints.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def create_auth_response(user):
    """Create authentication response with token and user data."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        'token': token.key,
        'fullname': user.profile.fullname,
        'email': user.email,
        'user_id': user.id
    }


class RegistrationView(APIView):
    """Handle user registration."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a new user and return token."""
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = create_auth_response(user)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Handle user login."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user and return token."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = self._authenticate_user(serializer.validated_data)
        if user:
            return Response(
                create_auth_response(user), status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Invalid'}, status=status.HTTP_400_BAD_REQUEST)

    def _authenticate_user(self, data):
        """Authenticate user by email and password."""
        try:
            user_obj = User.objects.get(email=data['email'])
            return authenticate(
                username=user_obj.username, password=data['password'])
        except User.DoesNotExist:
            return None


class EmailCheckView(APIView):
    """Check if email exists."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check if email is registered."""
        email = request.query_params.get('email', '')
        if not email:
            return Response(
                {'error': 'Required'}, status=status.HTTP_400_BAD_REQUEST)
        return self._find_user_by_email(email)

    def _find_user_by_email(self, email):
        """Find user by email and return response."""
        try:
            user = User.objects.get(email=email)
            return Response({
                'id': user.id,
                'email': user.email,
                'fullname': user.profile.fullname
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
