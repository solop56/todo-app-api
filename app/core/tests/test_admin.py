"""
Test for the Django admin modifications
"""
from typing import Any
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse


class AdminSiteTest(TestCase):
    """Test for Django admin"""

    # Test data constants
    ADMIN_EMAIL = 'admin@example.com'
    ADMIN_PASSWORD = 'testpass123'
    TEST_USER_EMAIL = 'user@example.com'
    TEST_USER_PASSWORD = 'testpass123'
    TEST_USER_NAME = 'Test User'

    def setUp(self) -> None:
        """Create user and client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email=self.ADMIN_EMAIL,
            password=self.ADMIN_PASSWORD
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email=self.TEST_USER_EMAIL,
            password=self.TEST_USER_PASSWORD,
            name=self.TEST_USER_NAME
        )

    def test_user_list(self) -> None:
        """Test that users are listed on page."""
        url = reverse('admin:core_user_changelist')
        res: HttpResponse = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)
        self.assertEqual(res.status_code, 200)

    def test_edit_user_page(self) -> None:
        """Test the edit user page works."""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res: HttpResponse = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'admin/change_form.html')

    def test_create_user_page(self) -> None:
        """Test the create user page works."""
        url = reverse('admin:core_user_add')
        res: HttpResponse = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'admin/change_form.html')