import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

CHAPA_API_URL = "https://api.chapa.co/v1/transaction/initialize"
CHAPA_VERIFY_URL = "https://api.chapa.co/v1/transaction/verify/"


def get_chapa_secret_key():
    return getattr(settings, "CHAPA_SECRET_KEY", "") or "CHASECK_TEST-LpIMynCSj89EOX7AgFurw1o6d7M9sLca"


def initialize_chapa_payment(tx_ref, amount, email, first_name, last_name, return_url, title="Job Portal Service", description="Payment for Job Portal services"):
    """
    Initializes a Chapa payment checkout session.
    Dynamically loads CHAPA_SECRET_KEY from settings.
    """
    import re

    secret_key = get_chapa_secret_key()

    if secret_key == "CHAPA_TEST_SECRET_KEY_MOCK" or not (secret_key.startswith("CHASECK") or secret_key.startswith("CHAPUBK")):
        logger.info("Chapa running in Mock Sandbox Mode.")
        return {
            "status": "success",
            "message": "Mock Chapa Checkout Session initialized",
            "checkout_url": f"{return_url}?tx_ref={tx_ref}&status=success&mock=true",
        }

    # Validate email - Chapa strictly requires a valid email format
    email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    if not email or not email_pattern.match(str(email).strip()):
        logger.warning(f"Invalid or missing email '{email}' for tx_ref {tx_ref}, using fallback.")
        email = f"user_{tx_ref[:8]}@ethiojobportal.com"

    clean_title = re.sub(r'[^a-zA-Z0-9\-_ \.]', '', str(title))[:16].strip() or "Job Portal"
    clean_desc = re.sub(r'[^a-zA-Z0-9\-_ \.]', '', str(description))[:50].strip() or "Payment for services."

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": email or "customer@ethiojobportal.com",
        "first_name": first_name or "User",
        "last_name": last_name or "Customer",
        "tx_ref": str(tx_ref),
        "return_url": return_url,
        "customization": {
            "title": clean_title,
            "description": clean_desc,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CHAPA_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("status") == "success":
                checkout_url = res_data.get("data", {}).get("checkout_url")
                logger.info(f"Chapa initialized successfully for {tx_ref}: {checkout_url}")
                return {
                    "status": "success",
                    "checkout_url": checkout_url,
                }
            logger.warning(f"Chapa API error response: {res_data}")
            return {"status": "error", "message": res_data.get("message", "Chapa initialization failed.")}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"Chapa API HTTP Error {e.code}: {err_body}")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("message") or err_body
        except Exception:
            msg = err_body
        return {
            "status": "error",
            "message": f"Chapa API Error ({e.code}): {msg}",
        }
    except Exception as e:
        logger.error(f"Chapa initialization network exception: {e}")
        return {
            "status": "error",
            "message": f"Payment Network Error: {str(e)}",
        }


def verify_chapa_payment(tx_ref):
    """
    Verifies a transaction using Chapa verification API.
    """
    secret_key = get_chapa_secret_key()
    if secret_key == "CHAPA_TEST_SECRET_KEY_MOCK" or not (secret_key.startswith("CHASECK") or secret_key.startswith("CHAPUBK")):
        return {"status": "success", "message": "Transaction verified (Mock)"}

    url = f"{CHAPA_VERIFY_URL}{tx_ref}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {secret_key}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("status") == "success":
                return {"status": "success", "data": res_data.get("data")}
            return {"status": "error", "message": res_data.get("message", "Verification failed.")}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"Chapa verify HTTP Error {e.code}: {err_body}")
        # 404 means Chapa has no record of this transaction (payment was not completed)
        if e.code == 404:
            return {"status": "error", "message": "Transaction not found. Payment may not have been completed."}
        return {"status": "error", "message": f"Verification error ({e.code}): {err_body[:200]}"}
    except urllib.error.URLError as e:
        # Network error during verification - fail safe (don't auto-approve)
        logger.error(f"Chapa verify network error: {e}")
        return {"status": "error", "message": f"Network error during verification: {str(e)}"}
    except Exception as e:
        logger.error(f"Chapa verify unexpected error: {e}")
        return {"status": "error", "message": str(e)}
