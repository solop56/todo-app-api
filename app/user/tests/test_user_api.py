"""
Test for the User API 
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status 


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token_obtain_pair')
TOKEN_RERESH_URL = reverse('user:token_refresh')
LOGOUT_URL = reverse('user:logout')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_successful(self):
        """Test creating a user is successful"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars"""
        payload = {
            'email': "test@example.com",
            'password': 'pw',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'test_user_password'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('access', res.data)   
        self.assertIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(email='test@example.com', password='goodpass')
        
        payload = {
            'email': 'test@example.com',
            'password': 'badpass'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('access', res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email"""
        payload = {'email': 'test@example.com', 'password': 'goodpass123'}
        res =  self.client.post(TOKEN_URL, payload)

        self.assertNotIn('access', payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_token_missing_fields(self):
        """Test returns error if email or password is missing."""
        res = self.client.post(TOKEN_URL, {'email':'test@example.com'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post(TOKEN_URL, {'password':'pass123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token(self):
        """Test refresh token returns a new access token."""
        user_details = {
            'email': 'test@example.com',
            'password': 'test_user_password',
            'name': 'Test Name'
        }
        create_user(**user_details)

        # Get initial token
        res = self.client.post(TOKEN_URL, {'email': user_details['email'], 'password': user_details['password']})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', res.data)

        refresh_payload = {'refresh': res.data['refresh']}
        refresh_res = self.client.post(TOKEN_RERESH_URL, refresh_payload)

        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_refresh_token_invalid(self):
        """Test refresh token fails with an invalid token."""
        refresh_payload = {'refresh': 'invalid_token'}
        res = self.client.post(TOKEN_RERESH_URL, refresh_payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_successful(self):
        """Test user logout with a valid refresh token."""
        user_details = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        create_user(**user_details)

        # Get tokens
        res = self.client.post(TOKEN_URL, {'email': user_details['email'], 'password': user_details['password']})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', res.data)  # ✅ Check refresh token exists

        refresh_token = res.data['refresh']

        # Send logout request with refresh token
        logout_res = self.client.post(LOGOUT_URL, {'refresh': refresh_token})

        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)  # ✅ Check for 200 OK

    def test_retrieve_user_unauthorized(self):
        """Test authication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API request that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='test@example.com', 
            password='testpass123',
            name='Test Name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_retrieve_profile_success(self):
        """Test retieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for me endpoint"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_user_profile(self):
        """Test updating the user profilefor the authenticated user"""
        payload = {'name': 'Updated name', 'password': 'newpassword123'}

        res = self.client.patch(ME_URL,payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)