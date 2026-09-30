from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from messaging.models import (
    Attachment,
    Message,
    MessageRecipient,
    MessageState,
)


class MessageSendingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sender = User.objects.create_user(
            username="sender",
            password="TestPassword123!",
            first_name="Ali",
            last_name="Sender",
            is_active=True,
        )

        cls.recipient = User.objects.create_user(
            username="recipient",
            password="TestPassword123!",
            first_name="Vali",
            last_name="Recipient",
            is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.sender)

    def test_user_can_send_message(self):
        response = self.client.post(
            reverse("compose"),
            {
                "action": "send",
                "recipient": self.recipient.id,
                "subject": "Test subject",
                "body": "Test message body",
            },
        )

        self.assertRedirects(
            response,
            reverse("inbox"),
        )

        message = Message.objects.get()

        self.assertEqual(
            message.sender,
            self.sender,
        )

        self.assertEqual(
            message.subject,
            "Test subject",
        )

        self.assertEqual(
            message.body,
            "Test message body",
        )

        self.assertEqual(
            message.status,
            Message.Status.SENT,
        )

        self.assertIsNotNone(
            message.sent_at,
        )

        recipient = MessageRecipient.objects.get(
            message=message,
        )

        self.assertEqual(
            recipient.recipient,
            self.recipient,
        )

        state = MessageState.objects.get(
            message=message,
            user=self.recipient,
        )

        self.assertFalse(
            state.is_read,
        )

    def test_recipient_sees_message_in_inbox(self):
        message = Message.objects.create(
            sender=self.sender,
            subject="Inbox test",
            body="Inbox message",
            status=Message.Status.SENT,
        )

        MessageRecipient.objects.create(
            message=message,
            recipient=self.recipient,
        )

        MessageState.objects.create(
            message=message,
            user=self.recipient,
        )

        self.client.force_login(self.recipient)

        response = self.client.get(
            reverse("inbox"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Inbox test",
        )

        self.assertContains(
            response,
            self.sender.first_name,
        )

    def test_recipient_can_open_message(self):
        message = Message.objects.create(
            sender=self.sender,
            subject="Detail test",
            body="Secret message",
            status=Message.Status.SENT,
        )

        MessageRecipient.objects.create(
            message=message,
            recipient=self.recipient,
        )

        MessageState.objects.create(
            message=message,
            user=self.recipient,
        )

        self.client.force_login(self.recipient)

        response = self.client.get(
            reverse(
                "message_detail",
                kwargs={"message_id": message.id},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Secret message",
        )

        state = MessageState.objects.get(
            message=message,
            user=self.recipient,
        )

        self.assertTrue(
            state.is_read,
        )

        self.assertIsNotNone(
            state.read_at,
        )

    def test_user_cannot_open_another_users_message(self):
        third_user = User.objects.create_user(
            username="third_user",
            password="TestPassword123!",
            first_name="Third",
            last_name="User",
            is_active=True,
        )

        message = Message.objects.create(
            sender=self.sender,
            subject="Private message",
            body="Private body",
            status=Message.Status.SENT,
        )

        MessageRecipient.objects.create(
            message=message,
            recipient=self.recipient,
        )

        MessageState.objects.create(
            message=message,
            user=self.recipient,
        )

        self.client.force_login(third_user)

        response = self.client.get(
            reverse(
                "message_detail",
                kwargs={"message_id": message.id},
            )
        )

        self.assertRedirects(
            response,
            reverse("inbox"),
        )

    def test_message_requires_recipient(self):
        response = self.client.post(
            reverse("compose"),
            {
                "action": "send",
                "recipient": "",
                "subject": "No recipient",
                "body": "Message body",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Message.objects.count(),
            0,
        )

    def test_message_requires_body(self):
        response = self.client.post(
            reverse("compose"),
            {
                "action": "send",
                "recipient": self.recipient.id,
                "subject": "Empty body",
                "body": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Message.objects.count(),
            0,
        )

    def test_draft_is_not_sent(self):
        response = self.client.post(
            reverse("compose"),
            {
                "action": "save_draft",
                "recipient": "",
                "subject": "Draft subject",
                "body": "Draft body",
            },
        )

        self.assertRedirects(
            response,
            reverse("drafts"),
        )

        message = Message.objects.get()

        self.assertEqual(
            message.status,
            Message.Status.DRAFT,
        )

        self.assertEqual(
            MessageRecipient.objects.count(),
            0,
        )

        self.assertEqual(
            MessageState.objects.count(),
            0,
        )