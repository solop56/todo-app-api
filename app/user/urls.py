"""
URL mapping for the user API.

This module defines all URL patterns related to user management including:
- User creation
- Authentication (login/logout)
- JWT token management
- User profile management
"""
from typing import List
from django.urls import path, URLPattern
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from user import views

app_name = 'user'

urlpatterns: List[URLPattern] = [
    # User management endpoints
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    
    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
