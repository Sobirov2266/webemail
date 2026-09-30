from django.test import TestCase

from accounts.models import DigitalKey, User


class DigitalKeyModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            first_name="Test",
            last_name="User",
        )

    def test_authentication_purpose_exists(self):
        self.assertEqual(
            DigitalKey.Purpose.AUTHENTICATION,
            "AUTHENTICATION",
        )

    def test_encryption_purpose_exists(self):
        self.assertEqual(
            DigitalKey.Purpose.ENCRYPTION,
            "ENCRYPTION",
        )