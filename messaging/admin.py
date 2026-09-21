from django.contrib import admin

from .models import Message, MessageRecipient, MessageState


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "subject",
        "status",
        "created_at",
        "sent_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "subject",
        "body",
        "sender__username",
        "sender__first_name",
        "sender__last_name",
    )


@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "recipient",
        "created_at",
    )

    search_fields = (
        "recipient__username",
        "recipient__first_name",
        "recipient__last_name",
        "message__subject",
    )


@admin.register(MessageState)
class MessageStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "user",
        "is_read",
        "is_starred",
        "is_archived",
        "is_deleted",
    )

    list_filter = (
        "is_read",
        "is_starred",
        "is_archived",
        "is_deleted",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "message__subject",
    )