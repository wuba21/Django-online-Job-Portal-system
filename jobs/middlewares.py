import time

from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from jobsapp.metrics import error_rates_counter, requests_total, last_user_activity_time, response_time_histogram


class CustomMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Exclude metrics endpoint from processing
        if "metrics" not in request.path:
            # Increment the Prometheus counter
            requests_total.labels(
                endpoint=request.path,
                method=request.method,
                user=request.user.get_username() if request.user.is_authenticated else "Anonymous",
            ).inc()

            # Update the last user activity time
            if request.user.is_authenticated:
                last_user_activity_time.labels(user=request.user.get_username()).set(now().timestamp())

        # Call the next middleware or view
        response = self.get_response(request)
        return response


class ResponseTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        response_time = time.time() - start_time

        response_time_histogram.labels(method=request.method, endpoint=request.path).observe(response_time)

        return response


class ErrorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 400 <= response.status_code < 600:
            error_rates_counter.labels(status_code=response.status_code, endpoint=request.path).inc()
        return response


import logging
from urllib.parse import quote
from django.apps import apps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

social_logger = logging.getLogger("social")

try:
    from social_core.exceptions import (
        SocialAuthBaseException,
        AuthStateMissing,
        AuthAlreadyAssociated,
        AuthCanceled,
        AuthFailed,
        AuthTokenError,
    )
except ImportError:
    SocialAuthBaseException = Exception
    AuthStateMissing = Exception
    AuthAlreadyAssociated = Exception
    AuthCanceled = Exception
    AuthFailed = Exception
    AuthTokenError = Exception


class CustomSocialAuthExceptionMiddleware:
    """
    Robust, production-grade Social Auth Exception Middleware.
    Catches all social authentication errors (including session drops,
    account association conflicts, user cancelations, network timeouts,
    and HTTP errors) and gracefully redirects users to the login page
    with professional, user-friendly feedback instead of throwing a 500 Server Error.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        path = getattr(request, "path", "")
        is_social_path = "/social-auth/" in path or hasattr(request, "social_strategy")

        is_social_exc = (
            isinstance(exception, SocialAuthBaseException)
            or "social" in exception.__class__.__module__.lower()
            or is_social_path
        )

        if not is_social_exc:
            return None

        backend = getattr(request, "backend", None)
        backend_name = getattr(backend, "name", "unknown")
        provider_display = "GitHub" if "github" in backend_name.lower() else "Google"

        if isinstance(exception, AuthCanceled):
            friendly_message = f"{provider_display} sign-in was canceled."
            message_tag = "info"
        elif isinstance(exception, AuthStateMissing):
            friendly_message = (
                f"Your {provider_display} authentication session timed out. "
                f"Please click Continue with {provider_display} to sign in."
            )
            message_tag = "warning"
        elif isinstance(exception, AuthAlreadyAssociated):
            friendly_message = (
                f"This {provider_display} account is already connected to an existing user. "
                f"Please sign in with your email or password."
            )
            message_tag = "warning"
        elif isinstance(exception, AuthFailed):
            err_text = str(exception)
            if "no account found" in err_text.lower() or "register first" in err_text.lower() or "አልተገኘም" in err_text:
                friendly_message = err_text
                message_tag = "not_registered"
            else:
                friendly_message = (
                    f"Unable to verify {provider_display} credentials. "
                    f"Please try again or log in with your email."
                )
                message_tag = "danger"
        elif isinstance(exception, AuthTokenError):
            friendly_message = (
                f"Unable to verify {provider_display} credentials. "
                f"Please try again or log in with your email."
            )
            message_tag = "danger"
        else:
            social_logger.warning(
                "Social auth exception caught for %s: %s: %s",
                backend_name,
                type(exception).__name__,
                str(exception),
            )
            friendly_message = (
                f"Unable to complete {provider_display} sign-in at this moment. "
                f"Please try again or sign in with your email and password."
            )
            message_tag = "warning"

        try:
            redirect_url = reverse("accounts:login")
        except Exception:
            redirect_url = "/en/login/"

        if apps.is_installed("django.contrib.messages"):
            try:
                if message_tag == "info":
                    messages.info(request, friendly_message, extra_tags=f"social-auth {backend_name}")
                elif message_tag == "warning":
                    messages.warning(request, friendly_message, extra_tags=f"social-auth {backend_name}")
                elif message_tag == "not_registered":
                    messages.error(request, friendly_message, extra_tags=f"not_registered social-auth {backend_name}")
                else:
                    messages.error(request, friendly_message, extra_tags=f"social-auth {backend_name}")
            except Exception:
                redirect_url += f"{'&' if '?' in redirect_url else '?'}auth_msg={quote(friendly_message)}"

        return redirect(redirect_url)

