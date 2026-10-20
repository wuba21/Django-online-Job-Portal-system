from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from jobsapp.models import ChatMessage, Conversation, Job, create_notification

User = get_user_model()


@login_required
def inbox_view(request):
    """
    Direct Messaging Inbox:
    2-Pane chat interface allowing employers and candidates to communicate
    in real time regarding applications, interviews, and job requirements.
    """
    user = request.user
    conversations = (
        Conversation.objects.filter(Q(employer=user) | Q(candidate=user))
        .select_related("employer", "candidate", "job")
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    conv_id = request.GET.get("c") or request.POST.get("conversation_id")
    active_conversation = None

    if conv_id:
        active_conversation = conversations.filter(id=conv_id).first()
    elif conversations.exists():
        active_conversation = conversations.first()

    # Process sending message
    if request.method == "POST" and active_conversation:
        body = request.POST.get("message", "").strip()
        if body:
            msg = ChatMessage.objects.create(
                conversation=active_conversation,
                sender=user,
                message=body
            )
            active_conversation.save()  # bumps updated_at

            # Notify the recipient
            recipient = active_conversation.get_other_user(user)
            create_notification(
                user=recipient,
                title=f"💬 New message from {user.get_full_name() or user.email}",
                message=body[:140],
                link=f"/messages/?c={active_conversation.id}"
            )

            # AJAX response support
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "status": "success",
                    "sender": user.get_full_name() or user.email,
                    "message": msg.message,
                    "created_at": msg.created_at.strftime("%H:%M"),
                })

            return redirect(f"/messages/?c={active_conversation.id}")

    # Mark active conversation messages as read
    active_messages = []
    if active_conversation:
        active_conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        active_messages = active_conversation.messages.select_related("sender").order_by("created_at")

    # Annotate unread counts for listing
    conversation_items = []
    for c in conversations:
        other_party = c.get_other_user(user)
        unread = c.messages.filter(is_read=False).exclude(sender=user).count()
        last_msg = c.messages.last()
        conversation_items.append({
            "obj": c,
            "other_user": other_party,
            "unread_count": unread,
            "last_message": last_msg,
        })

    context = {
        "conversations": conversation_items,
        "active_conversation": active_conversation,
        "active_messages": active_messages,
        "active_other_user": active_conversation.get_other_user(user) if active_conversation else None,
    }
    return render(request, "jobs/messages/inbox.html", context)


@login_required
def start_conversation(request, candidate_id):
    """
    Opens or creates a conversation with a candidate (from Employer ATS or Candidate profile).
    """
    candidate = get_object_or_404(User, id=candidate_id)
    user = request.user

    if user == candidate:
        messages.warning(request, "You cannot start a conversation with yourself.")
        return redirect("jobs:inbox")

    job_id = request.GET.get("job_id")
    job = get_object_or_404(Job, id=job_id) if job_id else None

    # Determine employer vs candidate roles
    if user.role == "employer":
        employer = user
        cand = candidate
    else:
        employer = candidate
        cand = user

    conv, created = Conversation.objects.get_or_create(
        employer=employer,
        candidate=cand,
        job=job
    )

    initial_msg = request.GET.get("intro")
    if initial_msg:
        ChatMessage.objects.create(
            conversation=conv,
            sender=user,
            message=initial_msg
        )
        conv.save()

    return redirect(f"/messages/?c={conv.id}")
