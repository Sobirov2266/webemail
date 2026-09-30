from django.urls import path
from .views import (
    inbox,
    compose,
    sent_messages,
    message_detail,
    drafts,
    download_attachment,
    starred,
    toggle_starred,
)

urlpatterns = [
    path("inbox/", inbox, name="inbox"),
    path("compose/", compose, name="compose"),
    path("sent/", sent_messages, name="sent_messages"),

    path(
        "message/<int:message_id>/",
        message_detail,
        name="message_detail",
    ),
    path(
        "drafts/",
        drafts,
        name="drafts",
    ),
    path(
        "attachments/<int:attachment_id>/download/",
        download_attachment,
        name="download_attachment",
    ),
    path(
        "starred/",
        starred,
        name="starred",
    ),
    path(
        "message/<int:message_id>/toggle-starred/",
        toggle_starred,
        name="toggle_starred",
    ),
]
