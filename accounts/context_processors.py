from django.conf import settings

def google_auth_settings(request):
    """
    Exposes Google OAuth Client ID to templates for Google One Tap and social login prompts.
    """
    return {
        "GOOGLE_CLIENT_ID": getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", ""),
    }
