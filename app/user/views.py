"""
Views for the user API
"""
from rest_framework import (
     generics, 
     status,
     authentication,
     permissions
)
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class LoginView(TokenObtainPairView):
    """Login for users"""
    serializer_class = AuthTokenSerializer


class LogoutView(generics.GenericAPIView):
    """Logout and Blacklist  the refresh token"""
    def post(self, request):
        """Post request for logout"""
        try:
                refresh_token = request.data.get('refresh')
                if not refresh_token:
                    return Response({'error':'Refresh token Required'}, status.HTTP_400_BAD_REQUEST)
                
                token = RefreshToken(refresh_token)
                token.blacklist()

                return Response({'message':'Logout Successful'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error':'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        

class ManageUserView(generics.RetrieveUpdateAPIView):
     """Manage the authenticated user."""
     serializer_class = UserSerializer
     authentication_classes = [authentication.TokenAuthentication]
     permission_classes = [permissions.IsAuthenticated]

     def get_object(self):
          """Retrieve and return the authenticated user."""
          return self.request.user