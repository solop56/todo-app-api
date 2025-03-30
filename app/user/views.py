"""
Views for the user API.

This module contains views for user management including:
- User creation
- Authentication (login/logout)
- User profile management
"""
from typing import Any
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework import serializers

from user.serializers import UserSerializer, AuthTokenSerializer, LogoutSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system.
    
    This view handles user registration with the following features:
    - Validates user input using UserSerializer
    - Throttles registration attempts to prevent abuse
    """
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]


class LoginView(TokenObtainPairView):
    """Login for users.
    
    This view handles user authentication and returns JWT tokens.
    It uses a custom serializer for additional validation.
    """
    serializer_class = AuthTokenSerializer
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        """Handle login request and return tokens with user data."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Get the validated user
            user = serializer.validated_data['user']
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Get user data using UserSerializer
            user_data = UserSerializer(user).data
            
            # Return tokens and user data
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
        except serializers.ValidationError as e:
            # Check if this is an authentication error
            if isinstance(e.detail, dict):
                for field, errors in e.detail.items():
                    if isinstance(errors, list) and any(
                        error.code == 'authorization' 
                        for error in errors
                    ):
                        return Response(
                            {'error': str(e)},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
            raise


class LogoutView(generics.GenericAPIView):
    """Logout and blacklist the refresh token.
    
    This view handles user logout by:
    - Validating the refresh token
    - Blacklisting the token to prevent reuse
    """
    serializer_class = LogoutSerializer
    throttle_classes = [UserRateThrottle]
    
    def post(self, request: Any) -> Response:
        """Handle logout request.
        
        Args:
            request: The HTTP request containing the refresh token
            
        Returns:
            Response: Success or error message with appropriate status code
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate and blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Successfully logged out'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user's profile.
    
    This view allows users to:
    - Retrieve their profile information
    - Update their profile details
    - Requires authentication for all operations
    """
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self) -> Any:
        """Retrieve and return the authenticated user.
        
        Returns:
            The currently authenticated user instance
        """
        return self.request.user