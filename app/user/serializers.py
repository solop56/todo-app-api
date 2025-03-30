"""
Serializers for the user API View
"""
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    created_at = serializers.DateTimeField(read_only=True, format=None)
    updated_at = serializers.DateTimeField(read_only=True, format=None)

    class Meta:
        model = get_user_model()
        fields = ['id', 'name', 'email', 'password', 'confirm_password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'name': {'min_length': 2}
        }

    def validate(self, attrs):
        """Validate user data"""
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError(
                {'password': 'Passwords do not match'},
                code='password_mismatch'
            )
        return attrs

    def create(self, validated_data):
        """Create and return a user with encrypted password"""
        validated_data.pop('confirm_password', None)
        user = get_user_model().objects.create_user(**validated_data)
        
        # Clear any cached user data
        cache_key = f'user_{user.id}'
        cache.delete(cache_key)
        
        return user
    
    def update(self, instance, validated_data):
        """Update and return user"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        # Convert dict_keys to list and handle password field
        update_fields = list(validated_data.keys())
        if password:
            update_fields.append('password')
        
        instance.save(update_fields=update_fields)
        
        # Clear any cached user data
        cache_key = f'user_{instance.id}'
        cache.delete(cache_key)
        
        return instance

    def to_representation(self, instance):
        """Convert instance to representation with datetime objects"""
        ret = super().to_representation(instance)
        ret.pop('password', None)
        ret.pop('confirm_password', None)
        # Ensure datetime fields are returned as datetime objects
        if isinstance(instance, get_user_model()):
            ret['created_at'] = instance.created_at
            ret['updated_at'] = instance.updated_at
        return ret


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    def validate(self, attrs):
        """Validate and authenticate user"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError(
                _('Please provide both email and password.'),
                code='authorization'
            )

        # Try to get user from cache first
        cache_key = f'user_auth_{email}'
        user = cache.get(cache_key)
        
        if not user:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if user:
                # Cache the authenticated user for 5 minutes
                cache.set(cache_key, user, timeout=300)
        
        if not user:
            raise serializers.ValidationError(
                _('Invalid credentials.'),
                code='authorization'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _('User account is disabled.'),
                code='authorization'
            )

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        """Convert the serializer instance to a dictionary."""
        data = super().to_representation(instance)
        user = instance.get('user')
        if user:
            data['user'] = UserSerializer(user).data
        return data


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout request."""
    refresh_token = serializers.CharField(required=True)
    