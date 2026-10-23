from django.db.models import Q
from jobsapp.models import ChatMessage, Notification


def notifications_context(request):
    """
    Globally provides unread notification counts and unread message counts
    for the authenticated user.
    """
    if request.user.is_authenticated:
        unread_qs = Notification.objects.filter(user=request.user, is_read=False)
        unread_msgs = (
            ChatMessage.objects.filter(
                Q(conversation__employer=request.user) | Q(conversation__candidate=request.user),
                is_read=False,
            )
            .exclude(sender=request.user)
            .count()
        )
        return {
            "unread_notifications_count": unread_qs.count(),
            "recent_unread_notifications": unread_qs[:5],
            "unread_messages_count": unread_msgs,
        }
    return {
        "unread_notifications_count": 0,
        "recent_unread_notifications": [],
        "unread_messages_count": 0,
    }
