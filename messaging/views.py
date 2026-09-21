from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch

from accounts.models import User

from .models import Message, MessageRecipient, MessageState


@login_required(login_url="user_login")
def inbox(request):

    recipients = (
        MessageRecipient.objects
        .filter(
            recipient=request.user,
            message__status=Message.Status.SENT,
        )
        .select_related(
            "message",
            "message__sender",
        )
        .prefetch_related(
            Prefetch(
                "message__states",
                queryset=MessageState.objects.filter(
                    user=request.user
                ),
                to_attr="current_user_states",
            )
        )
    )

    return render(
        request,
        "messaging/inbox.html",
        {
            "recipients": recipients,
        }
    )


@login_required(login_url="user_login")
def message_detail(request, message_id):

    try:
        recipient = (
            MessageRecipient.objects
            .select_related(
                "message",
                "message__sender",
                "recipient",
            )
            .get(
                message_id=message_id,
                recipient=request.user,
            )
        )
    except MessageRecipient.DoesNotExist:
        return redirect("inbox")

    message = recipient.message

    state, created = MessageState.objects.get_or_create(
        message=message,
        user=request.user,
    )

    if not state.is_read:
        state.is_read = True
        state.read_at = timezone.now()
        state.save(
            update_fields=["is_read", "read_at"]
        )

    return render(
        request,
        "messaging/message_detail.html",
        {
            "message": message,
            "recipient": recipient,
        }
    )


@login_required(login_url="user_login")
def compose(request):

    users = (
        User.objects
        .filter(is_active=True, is_superuser=False)
        .select_related("department__organization")
        .order_by("last_name", "first_name")
    )

    if request.method == "POST":

        recipient_id = request.POST.get("recipient")
        subject = request.POST.get("subject", "").strip()
        body = request.POST.get("body", "").strip()

        if not recipient_id:
            return render(
                request,
                "messaging/compose.html",
                {
                    "users": users,
                    "error": "Qabul qiluvchini tanlang."
                }
            )

        if not body:
            return render(
                request,
                "messaging/compose.html",
                {
                    "users": users,
                    "error": "Xabar matnini kiriting."
                }
            )

        try:
            recipient = User.objects.get(
                id=recipient_id,
                is_active=True,
                is_superuser=False,
            )
        except User.DoesNotExist:
            return render(
                request,
                "messaging/compose.html",
                {
                    "users": users,
                    "error": "Qabul qiluvchi topilmadi."
                }
            )

        with transaction.atomic():

            message = Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body,
                status=Message.Status.SENT,
                sent_at=timezone.now(),
            )

            MessageRecipient.objects.create(
                message=message,
                recipient=recipient,
            )

            MessageState.objects.create(
                message=message,
                user=recipient,
            )

        return redirect("inbox")

    return render(
        request,
        "messaging/compose.html",
        {
            "users": users,
        }
    )


@login_required(login_url="user_login")
def sent_messages(request):

    messages = (
        Message.objects
        .filter(
            sender=request.user,
            status=Message.Status.SENT,
        )
        .prefetch_related(
            "recipients__recipient",
        )
    )

    return render(
        request,
        "messaging/sent.html",
        {
            "messages": messages,
        }
    )