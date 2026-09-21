from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User

from .models import Attachment, Message, MessageRecipient, MessageState


class MessagingFlowTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username="sender",
            password="test-password",
            first_name="Sender",
            last_name="User",
        )
        self.recipient = User.objects.create_user(
            username="recipient",
            password="test-password",
            first_name="Recipient",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="test-password",
            first_name="Other",
            last_name="User",
        )

    def create_sent_message(self, sender, recipient, subject="Test xat"):
        message = Message.objects.create(
            sender=sender,
            subject=subject,
            body="Xabar matni",
            status=Message.Status.SENT,
        )
        MessageRecipient.objects.create(message=message, recipient=recipient)
        MessageState.objects.create(message=message, user=recipient)
        return message

    def test_compose_hides_current_user_from_recipient_list(self):
        self.client.force_login(self.sender)

        response = self.client.get(reverse("compose"))

        self.assertContains(response, self.recipient.first_name)
        self.assertNotContains(
            response,
            f'<option value="{self.sender.id}">',
            html=False,
        )

    def test_compose_rejects_a_manually_submitted_self_recipient(self):
        self.client.force_login(self.sender)

        response = self.client.post(
            reverse("compose"),
            {
                "action": "send",
                "recipient": self.sender.id,
                "subject": "Sinov",
                "body": "Xabar",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qabul qiluvchi topilmadi.")
        self.assertFalse(Message.objects.filter(sender=self.sender).exists())

    def test_dashboard_shows_message_statistics(self):
        received_message = self.create_sent_message(
            self.other_user,
            self.sender,
        )
        MessageState.objects.filter(
            message=received_message,
            user=self.sender,
        ).update(is_starred=True)
        self.create_sent_message(self.sender, self.recipient)
        Message.objects.create(
            sender=self.sender,
            subject="Qoralama",
            body="Keyinroq yuboriladi",
            status=Message.Status.DRAFT,
        )
        self.client.force_login(self.sender)

        response = self.client.get(reverse("user_dashboard"))

        self.assertEqual(response.context["inbox_count"], 1)
        self.assertEqual(response.context["sent_count"], 1)
        self.assertEqual(response.context["draft_count"], 1)
        self.assertEqual(response.context["saved_count"], 1)

    def test_attachment_download_requires_the_message_recipient(self):
        message = self.create_sent_message(self.sender, self.recipient)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                attachment = Attachment.objects.create(
                    message=message,
                    file=SimpleUploadedFile(
                        "xabar.txt",
                        b"maxfiy xabar",
                        content_type="text/plain",
                    ),
                    original_name="xabar.txt",
                    file_size=13,
                )

                self.client.force_login(self.other_user)
                forbidden_response = self.client.get(
                    reverse("download_attachment", args=[attachment.id])
                )

                self.client.force_login(self.recipient)
                allowed_response = self.client.get(
                    reverse("download_attachment", args=[attachment.id])
                )

                allowed_response.close()
                direct_response = self.client.get(attachment.file.url)

        self.assertEqual(forbidden_response.status_code, 404)
        self.assertEqual(allowed_response.status_code, 200)
        self.assertEqual(direct_response.status_code, 404)
        self.assertEqual(
            allowed_response["Content-Disposition"],
            'attachment; filename="xabar.txt"',
        )
