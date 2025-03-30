"""
Test suite for the User API endpoints.

This module contains tests for user-related API endpoints including:
- User registration
- Authentication (login, logout, token refresh)
- User profile management
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

from rest_framework.test import APIClient
from rest_framework import status

# API Endpoint URLs
CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:login')
TOKEN_RERESH_URL = reverse('user:token_refresh')
LOGOUT_URL = reverse('user:logout')
ME_URL = reverse('user:me')

# Test Data
VALID_USER_PAYLOAD = {
    'email': 'test@example.com',
    'password': 'testpass123',
    'confirm_password': 'testpass123',
    'name': 'Test User',
}

VALID_USER_DETAILS = {
    'name': 'Test Name',
    'email': 'test@example.com',
    'password': 'test_user_password',
    'confirm_password': 'test_user_password'
}

VALID_LOGIN_PAYLOAD = {
    'email': 'test@example.com',
    'password': 'test_user_password'
}

VALID_PROFILE_UPDATE_PAYLOAD = {
    'name': 'Updated name',
    'password': 'newpassword123',
    'confirm_password': 'newpassword123'
}

PARTIAL_PROFILE_UPDATE_PAYLOAD = {
    'name': 'New Name'
}

# Helper Functions
def create_user(**params):
    """Create and return a new user with the given parameters."""
    # Remove confirm_password if present as it's not needed for direct user creation
    params = params.copy()
    params.pop('confirm_password', None)
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test suite for public user API endpoints (no authentication required)."""

    def setUp(self):
        """Set up test client and clear cache before each test."""
        self.client = APIClient()
        cache.clear()

    def tearDown(self):
        """Clean up cache after each test."""
        cache.clear()

    # User Registration Tests
    def test_create_user_successful(self):
        """Test successful user registration with valid data."""
        res = self.client.post(CREATE_USER_URL, VALID_USER_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=VALID_USER_PAYLOAD['email'])
        self.assertTrue(user.check_password(VALID_USER_PAYLOAD['password']))
        self.assertNotIn('password', res.data)
        self.assertNotIn('confirm_password', res.data)

    def test_user_with_email_exists_error(self):
        """Test registration fails when email already exists."""
        create_user(**VALID_USER_DETAILS)
        res = self.client.post(CREATE_USER_URL, VALID_USER_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_too_short_error(self):
        """Test registration fails when password is too short."""
        payload = {
            **VALID_USER_PAYLOAD,
            'password': 'pw',
            'confirm_password': 'pw'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)

    def test_password_mismatch_error(self):
        """Test registration fails when passwords don't match."""
        payload = {
            **VALID_USER_PAYLOAD,
            'confirm_password': 'differentpass'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)

    # Authentication Tests
    def test_create_token_for_user(self):
        """Test successful token generation with valid credentials."""
        create_user(**VALID_USER_DETAILS)
        res = self.client.post(TOKEN_URL, VALID_LOGIN_PAYLOAD)

        self.assertIn('access', res.data)   
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test token generation fails with invalid credentials."""
        create_user(email='test@example.com', password='goodpass')
        
        payload = {
            'email': 'test@example.com',
            'password': 'badpass'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('access', res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_email_not_found(self):
        """Test token generation fails when user doesn't exist."""
        payload = {'email': 'test@example.com', 'password': 'goodpass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('access', res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_token_missing_fields(self):
        """Test token generation fails when required fields are missing."""
        res = self.client.post(TOKEN_URL, {'email':'test@example.com'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post(TOKEN_URL, {'password':'pass123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # Token Refresh Tests
    def test_refresh_token(self):
        """Test successful token refresh with valid refresh token."""
        create_user(**VALID_USER_DETAILS)

        # Get initial token
        res = self.client.post(TOKEN_URL, VALID_LOGIN_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', res.data)

        refresh_payload = {'refresh': res.data['refresh']}
        refresh_res = self.client.post(TOKEN_RERESH_URL, refresh_payload)

        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_refresh_token_invalid(self):
        """Test token refresh fails with invalid refresh token."""
        refresh_payload = {'refresh': 'invalid_token'}
        res = self.client.post(TOKEN_RERESH_URL, refresh_payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # Logout Tests
    def test_logout_successful(self):
        """Test successful user logout with valid refresh token."""
        create_user(**VALID_USER_DETAILS)

        # Get tokens
        res = self.client.post(TOKEN_URL, VALID_LOGIN_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', res.data)

        refresh_token = res.data['refresh']

        # Send logout request with refresh token
        logout_res = self.client.post(LOGOUT_URL, {'refresh': refresh_token})

        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

    # Profile Access Tests
    def test_retrieve_user_unauthorized(self):
        """Test profile access requires authentication."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test suite for private user API endpoints (authentication required)."""

    def setUp(self):
        """Set up test client, create test user, and authenticate."""
        self.user = create_user(**VALID_USER_DETAILS)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def tearDown(self):
        """Clean up cache after each test."""
        cache.clear()
    
    # Profile Retrieval Tests
    def test_retrieve_profile_success(self):
        """Test successful profile retrieval for authenticated user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'id': self.user.id,
            'name': self.user.name,
            'email': self.user.email,
            'created_at': self.user.created_at,
            'updated_at': self.user.updated_at
        })

    def test_post_me_not_allowed(self):
        """Test POST method is not allowed for profile endpoint."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # Profile Update Tests
    def test_update_user_profile(self):
        """Test successful full profile update."""
        res = self.client.patch(ME_URL, VALID_PROFILE_UPDATE_PAYLOAD)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, VALID_PROFILE_UPDATE_PAYLOAD['name'])
        self.assertTrue(self.user.check_password(VALID_PROFILE_UPDATE_PAYLOAD['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_user_profile_partial(self):
        """Test successful partial profile update."""
        res = self.client.patch(ME_URL, PARTIAL_PROFILE_UPDATE_PAYLOAD)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, PARTIAL_PROFILE_UPDATE_PAYLOAD['name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)