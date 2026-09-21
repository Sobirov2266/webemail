from django.conf import settings
from django.db import models
from django.utils import timezone


class Message(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Qoralama"
        SENT = "SENT", "Yuborilgan"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
        verbose_name="Yuboruvchi"
    )

    subject = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Mavzu"
    )

    body = models.TextField(
        blank=True,
        verbose_name="Xabar matni"
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="O‘zgartirilgan vaqt"
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Yuborilgan vaqt"
    )

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Javob berilgan xabar"
    )

    forwarded_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forwards",
        verbose_name="Forward qilingan xabar"
    )

    class Meta:
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ["-created_at"]

    def __str__(self):
        if self.subject:
            return self.subject

        return f"Xabar #{self.id}"

    def mark_as_sent(self):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "sent_at",
                "updated_at",
            ]
        )


class MessageRecipient(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Xabar"
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_messages",
        verbose_name="Qabul qiluvchi"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yuborilgan vaqt"
    )

    class Meta:
        verbose_name = "Xabar qabul qiluvchisi"
        verbose_name_plural = "Xabar qabul qiluvchilari"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "recipient"],
                name="unique_message_recipient"
            )
        ]

    def __str__(self):
        return (
            f"{self.message} → "
            f"{self.recipient}"
        )


class MessageState(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="states",
        verbose_name="Xabar"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_states",
        verbose_name="Foydalanuvchi"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="O‘qilgan"
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="O‘qilgan vaqt"
    )

    is_starred = models.BooleanField(
        default=False,
        verbose_name="Belgilangan"
    )

    is_archived = models.BooleanField(
        default=False,
        verbose_name="Arxivlangan"
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name="O‘chirilgan"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    class Meta:
        verbose_name = "Xabar holati"
        verbose_name_plural = "Xabar holatlari"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_message_state_per_user"
            )
        ]

    def __str__(self):
        return (
            f"{self.user} — "
            f"{self.message}"
        )



