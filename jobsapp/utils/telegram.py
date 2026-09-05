import json
import urllib.request
import urllib.parse
from django.conf import settings


def broadcast_job_to_telegram(job, domain="https://wubante.pythonanywhere.com"):
    """
    Broadcasts a newly posted or approved job vacancy to Telegram Channel / Bot.
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from settings.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[Telegram Broadcast] Skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return False

    if getattr(job, "slug", None):
        job_url = f"{domain}/{job.slug}/"
    else:
        job_url = f"{domain}/en/jobs/{job.id}/"

    salary_text = f"{job.salary:,} {job.currency}" if job.salary > 0 else "Negotiable"

    message_html = (
        f"🚨 <b>NEW VACANCY ALERT</b> 🚨\n\n"
        f"💼 <b>Title:</b> {job.title}\n"
        f"🏢 <b>Company:</b> {job.company_name}\n"
        f"📍 <b>Location:</b> {job.location}\n"
        f"💵 <b>Salary:</b> {salary_text}\n"
        f"⏳ <b>Deadline:</b> {job.last_date.strftime('%b %d, %Y')}\n\n"
        f"👉 <a href='{job_url}'>Click Here to Apply on Portal</a>"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"[Telegram Broadcast] Success: {res.get('ok', False)}")
            return res.get("ok", False)
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8", errors="ignore")
        print(f"[Telegram Broadcast HTTP Error {he.code}]: {err_body}")
        return False
    except Exception as e:
        print(f"[Telegram Broadcast Error]: {e}")
        return False
