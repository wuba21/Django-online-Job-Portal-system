import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)


def broadcast_job_to_telegram(job, domain="https://wubante.pythonanywhere.com"):
    """
    Broadcasts a newly posted or approved job vacancy to Telegram Channel / Bot.
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from settings.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or env_fallback("TELEGRAM_BOT_TOKEN")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or env_fallback("TELEGRAM_CHAT_ID") or "@ethio_jobportal"

    if not bot_token:
        logger.warning("Telegram broadcast skipped: TELEGRAM_BOT_TOKEN is not configured.")
        return False

    if getattr(job, "slug", None):
        job_url = f"{domain}/jobs/{job.slug}/"
    else:
        job_url = f"{domain}/en/jobs/{job.id}/"

    salary_val = getattr(job, "salary", 0) or 0
    salary_text = f"{salary_val:,} {getattr(job, 'currency', 'ETB')}" if salary_val > 0 else "Negotiable"
    company_name = getattr(job, "company_name", "") or (job.company.name if getattr(job, "company", None) else "Company")

    message_html = (
        f"🚨 <b>NEW VACANCY ALERT</b> 🚨\n\n"
        f"💼 <b>Title:</b> {job.title}\n"
        f"🏢 <b>Company:</b> {company_name}\n"
        f"📍 <b>Location:</b> {job.location}\n"
        f"💵 <b>Salary:</b> {salary_text}\n"
        f"⏳ <b>Deadline:</b> {job.last_date.strftime('%b %d, %Y') if getattr(job, 'last_date', None) else 'N/A'}\n\n"
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
            ok = res.get("ok", False)
            if ok:
                logger.info(f"Telegram broadcast successful for job '{job.title}' to {chat_id}")
            else:
                logger.warning(f"Telegram API response not OK: {res}")
            return ok
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"Telegram API HTTP Error {e.code}: {err_body}")
        print(f"Telegram API HTTP Error {e.code}: {err_body}")
        return False
    except Exception as e:
        logger.error(f"Telegram broadcast network error: {e}")
        print(f"Telegram broadcast network error: {e}")
        return False


def env_fallback(key):
    try:
        from django.conf import settings
        return getattr(settings, "env", lambda k, default="": default)(key, default="")
    except Exception:
        return ""
