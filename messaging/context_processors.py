from .models import MessageState


def unread_count(request):

    if not request.user.is_authenticated:
        return {
            "unread_count": 0,
        }

    count = MessageState.objects.filter(
        user=request.user,
        is_read=False,
        is_deleted=False,
        is_archived=False,
    ).count()

    return {
        "unread_count": count,
    }