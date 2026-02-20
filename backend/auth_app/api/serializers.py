"""
Serializers for authentication endpoints.
"""
from django.contrib.auth.models import User

from rest_framework import serializers

from auth_app.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User with profile data."""
    fullname = serializers.CharField(source='profile.fullname', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class RegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""
    fullname = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate(self, attrs):
        """Check if passwords match."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({
                "repeated_password": "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        """Create and return a new user with profile."""
        fullname = validated_data.pop('fullname')
        validated_data.pop('repeated_password')
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password']
        )
        user.profile.fullname = fullname
        user.profile.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
