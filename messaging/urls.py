from django.urls import path
from .views import (
    inbox,
    compose,
    sent_messages,
    message_detail,
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
]