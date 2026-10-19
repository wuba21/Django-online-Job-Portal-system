import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)


def broadcast_job_to_telegram(job, domain=None, request=None, return_detail=False):
    """
    Broadcasts a newly posted or approved job vacancy to Telegram Channel / Bot.
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from settings.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or env_fallback("TELEGRAM_BOT_TOKEN")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or env_fallback("TELEGRAM_CHAT_ID") or "-1003318389514"

    # Always ensure valid target channel ID even if cache/old settings had @ethio_jobportal
    if str(chat_id).strip() in ["@ethio_jobportal", ""]:
        chat_id = "-1003318389514"

    if not bot_token:
        err = "TELEGRAM_BOT_TOKEN is not configured in settings or .env."
        logger.warning(f"Telegram broadcast skipped: {err}")
        return (False, err) if return_detail else False

    # Resolve target portal domain dynamically
    if not domain:
        if request is not None:
            domain = request.build_absolute_uri('/')[:-1]
        else:
            domain = getattr(settings, "SITE_URL", "") or "https://wubante.pythonanywhere.com"
    domain = domain.rstrip("/")

    # Use /jobs/<id>/ which redirects directly and reliably in all environments
    job_url = f"{domain}/jobs/{job.id}/"

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
        with urllib.request.urlopen(req, timeout=25) as response:
            res = json.loads(response.read().decode("utf-8"))
            ok = res.get("ok", False)
            if ok:
                logger.info(f"Telegram broadcast successful for job '{job.title}' to {chat_id}")
                return (True, "Delivered to Telegram") if return_detail else True
            else:
                desc = res.get("description", "Unknown Telegram API response")
                logger.warning(f"Telegram API response not OK: {res}")
                return (False, desc) if return_detail else False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            err_desc = err_json.get("description", err_body)
        except Exception:
            err_desc = err_body
        logger.error(f"Telegram API HTTP Error {e.code}: {err_desc}")
        return (False, f"HTTP {e.code}: {err_desc}") if return_detail else False
    except Exception as e:
        logger.error(f"Telegram broadcast network error: {e}")
        return (False, str(e)) if return_detail else False


def env_fallback(key):
    try:
        from django.conf import settings
        return getattr(settings, "env", lambda k, default="": default)(key, default="")
    except Exception:
        return ""
