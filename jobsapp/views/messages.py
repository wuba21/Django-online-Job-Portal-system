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
            if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.POST.get("ajax"):
                return JsonResponse({
                    "status": "success",
                    "id": msg.id,
                    "sender": user.get_full_name() or user.email,
                    "message": msg.message,
                    "created_at": msg.created_at.strftime("%b %d, %H:%M"),
                    "is_me": True,
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

    # Available contacts for starting a new conversation
    contacts = []
    user_jobs = []
    if user.role == "employer":
        applied_candidates = list(
            User.objects.filter(applicant__job__user=user)
            .exclude(id=user.id)
            .distinct()[:50]
        )
        if len(applied_candidates) < 15:
            other_cands = list(
                User.objects.filter(role="employee", is_active=True)
                .exclude(id=user.id)
                .exclude(id__in=[u.id for u in applied_candidates])[:30]
            )
            contacts = applied_candidates + other_cands
        else:
            contacts = applied_candidates
        user_jobs = Job.objects.filter(user=user).order_by("-created_at")[:20]
    else:
        applied_employers = list(
            User.objects.filter(job__applicants__user=user)
            .exclude(id=user.id)
            .distinct()[:50]
        )
        if len(applied_employers) < 15:
            other_emps = list(
                User.objects.filter(role="employer", is_active=True)
                .exclude(id=user.id)
                .exclude(id__in=[u.id for u in applied_employers])[:30]
            )
            contacts = applied_employers + other_emps
        else:
            contacts = applied_employers
        user_jobs = Job.objects.filter(applicants__user=user).distinct()[:20]

    context = {
        "conversations": conversation_items,
        "active_conversation": active_conversation,
        "active_messages": active_messages,
        "active_other_user": active_conversation.get_other_user(user) if active_conversation else None,
        "contacts": contacts,
        "user_jobs": user_jobs,
    }
    return render(request, "jobs/messages/inbox.html", context)


@login_required
def start_conversation(request, candidate_id=None):
    """
    Opens or creates a conversation with a candidate/employer (from ATS, Job details, or Inbox modal).
    """
    if not candidate_id:
        candidate_id = request.POST.get("recipient_id") or request.GET.get("recipient_id")

    candidate = get_object_or_404(User, id=candidate_id)
    user = request.user

    if user == candidate:
        messages.warning(request, "You cannot start a conversation with yourself.")
        return redirect("jobs:inbox")

    job_id = request.POST.get("job_id") or request.GET.get("job_id")
    job = Job.objects.filter(id=job_id).first() if job_id else None

    # Determine employer vs candidate roles consistently
    if user.role == "employer" and candidate.role != "employer":
        employer = user
        cand = candidate
    elif candidate.role == "employer" and user.role != "employer":
        employer = candidate
        cand = user
    elif user.id < candidate.id:
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

    initial_msg = (request.POST.get("message") or request.GET.get("intro") or "").strip()
    if initial_msg:
        ChatMessage.objects.create(
            conversation=conv,
            sender=user,
            message=initial_msg
        )
        conv.save()
        create_notification(
            user=candidate,
            title=f"💬 New message from {user.get_full_name() or user.email}",
            message=initial_msg[:140],
            link=f"/messages/?c={conv.id}"
        )

    return redirect(f"/messages/?c={conv.id}")


@login_required
def poll_messages(request, conversation_id):
    """
    Real-time auto-fetch endpoint for chat messages without needing full page reloads.
    Returns messages sent after `last_id`.
    """
    conv = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    if user != conv.employer and user != conv.candidate and not user.is_staff:
        return JsonResponse({"error": "unauthorized"}, status=403)

    last_id = int(request.GET.get("last_id", 0))
    new_messages = (
        conv.messages.filter(id__gt=last_id)
        .select_related("sender")
        .order_by("created_at")
    )

    # Mark unread incoming messages as read
    conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    data = []
    for m in new_messages:
        data.append({
            "id": m.id,
            "sender_name": m.sender.get_full_name() or m.sender.email,
            "sender_id": m.sender.id,
            "message": m.message,
            "created_at": m.created_at.strftime("%b %d, %H:%M"),
            "is_me": m.sender == user,
        })

    return JsonResponse({
        "status": "success",
        "messages": data,
        "count": len(data)
    })
