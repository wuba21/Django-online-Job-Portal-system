from jobsapp.models import Notification


def notifications_context(request):
    """
    Globally provides unread notification counts and latest unread notifications
    for the authenticated user.
    """
    if request.user.is_authenticated:
        unread_qs = Notification.objects.filter(user=request.user, is_read=False)
        return {
            "unread_notifications_count": unread_qs.count(),
            "recent_unread_notifications": unread_qs[:5],
        }
    return {
        "unread_notifications_count": 0,
        "recent_unread_notifications": [],
    }
