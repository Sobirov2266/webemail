from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch

from accounts.models import User

from .models import (
    Message,
    MessageRecipient,
    MessageState,
    Attachment,
)


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
        .filter(
            is_active=True,
            is_superuser=False,
        )
        .exclude(
            id=request.user.id,
        )
        .select_related(
            "department__organization",
        )
        .order_by(
            "last_name",
            "first_name",
        )
    )

    if request.method == "POST":

        action = request.POST.get(
            "action",
            "send",
        )

        recipient_id = request.POST.get(
            "recipient"
        )

        subject = request.POST.get(
            "subject",
            "",
        ).strip()

        body = request.POST.get(
            "body",
            "",
        ).strip()

        attachment = request.FILES.get(
            "attachment"
        )


        # ==================================================
        # FAYL CHEK
        # ==================================================

        if attachment:

            max_file_size = 10 * 1024 * 1024

            allowed_extensions = {
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".txt",
                ".jpg",
                ".jpeg",
                ".png",
            }

            file_name = attachment.name.lower()

            if attachment.size > max_file_size:

                return render(
                    request,
                    "messaging/compose.html",
                    {
                        "users": users,
                        "error": (
                            "Fayl hajmi 10 MB "
                            "dan oshmasligi kerak."
                        ),
                    },
                )

            import os

            file_extension = os.path.splitext(
                file_name
            )[1]

            if file_extension not in allowed_extensions:

                return render(
                    request,
                    "messaging/compose.html",
                    {
                        "users": users,
                        "error": (
                            "Bu fayl formatiga "
                            "ruxsat berilmagan."
                        ),
                    },
                )


        # ==================================================
        # QORALAMAGA SAQLASH
        # ==================================================

        if action == "save_draft":

            with transaction.atomic():

                message = Message.objects.create(
                    sender=request.user,
                    subject=subject,
                    body=body,
                    status=Message.Status.DRAFT,
                )

                if attachment:

                    Attachment.objects.create(
                        message=message,
                        file=attachment,
                        original_name=attachment.name,
                        file_size=attachment.size,
                    )

            return redirect("drafts")


        # ==================================================
        # YUBORISH UCHUN VALIDATSIYA
        # ==================================================

        if not recipient_id:

            return render(
                request,
                "messaging/compose.html",
                {
                    "users": users,
                    "error": (
                        "Qabul qiluvchini tanlang."
                    ),
                },
            )


        if not body:

            return render(
                request,
                "messaging/compose.html",
                {
                    "users": users,
                    "error": (
                        "Xabar matnini kiriting."
                    ),
                },
            )


        # ==================================================
        # QABUL QILUVCHINI TOPISH
        # ==================================================

        try:

            recipient = User.objects.exclude(
                id=request.user.id,
            ).get(
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
                    "error": (
                        "Qabul qiluvchi topilmadi."
                    ),
                },
            )


        # ==================================================
        # XATNI YUBORISH
        # ==================================================

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


            if attachment:

                Attachment.objects.create(
                    message=message,
                    file=attachment,
                    original_name=attachment.name,
                    file_size=attachment.size,
                )


        return redirect("inbox")


    return render(
        request,
        "messaging/compose.html",
        {
            "users": users,
        },
    )



@login_required(login_url="user_login")
def drafts(request):

    messages = (
        Message.objects
        .filter(
            sender=request.user,
            status=Message.Status.DRAFT,
        )
        .prefetch_related(
            "attachments",
        )
        .order_by("-updated_at")
    )

    return render(
        request,
        "messaging/drafts.html",
        {
            "messages": messages,
        },
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


@login_required(login_url="user_login")
def download_attachment(request, attachment_id):
    attachment = get_object_or_404(
        Attachment.objects.select_related("message"),
        id=attachment_id,
        message__recipients__recipient=request.user,
    )

    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=attachment.original_name,
    )
