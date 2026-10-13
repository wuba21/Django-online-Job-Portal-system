import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password

# Known disposable, temporary, and test email domains
DISPOSABLE_EMAIL_DOMAINS = {
    # Testing & Placeholder domains
    "test.com", "example.com", "example.org", "example.net",
    "fake.com", "dummy.com", "sample.com", "invalid.com",
    "none.com", "asdf.com", "test.org", "fake.org",
    "test.net", "fake.net", "admin.com", "user.com",
    "xyz.com", "temp.com", "testing.com", "demo.com",
    "mail.com.invalid", "foo.com", "bar.com", "localhost",
    # Temporary / Disposable / Burner Services
    "mailinator.com", "tempmail.com", "temp-mail.org", "10minutemail.com",
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org", "guerrillamail.biz",
    "sharklasers.com", "grr.la", "guerrillamailblock.com", "pokemail.net",
    "trashmail.com", "trashmail.net", "trashmail.me", "yopmail.com", "yopmail.fr",
    "yopmail.net", "dispostable.com", "throwawaymail.com", "getnada.com",
    "fakemailgenerator.com", "emailondeck.com", "mohmal.com", "crazymailing.com",
    "throwaway.email", "generator.email", "mytemp.email", "spam4.me", "maildrop.cc",
    "inboxkitten.com", "dropmail.me", "burnermail.io", "nada.ltd", "getairmail.com",
    "tempinbox.com", "discard.email", "disposablemail.com", "fakemail.net",
    "trashinbox.com", "mytempmail.com", "nada.email", "0-mail.com", "meltmail.com",
    "harakirimail.com", "mytempemail.com", "tempail.com", "tempemail.co",
    "fakemail.org", "minuteinbox.com", "emailfake.com", "incognitomail.com",
}

FAKE_USERNAMES = {
    "test", "testing", "tester", "fake", "dummy", "sample",
    "asdf", "asdfg", "asdfgh", "qwerty", "admin", "administrator",
    "user", "anonymous", "nobody", "null", "123456", "12345678",
    "random", "junk", "trash", "temp", "tempuser", "employee",
    "employer", "demo", "samplemail", "testmail"
}


def validate_legitimate_email(email):
    """
    Validates that the provided email is a legitimate, active email
    and not a disposable, dummy, or fake address.
    Specifically validates Google/Gmail format and standard corporate/personal domains.
    """
    if not email:
        raise ValidationError("Email address is required.")

    email = email.strip().lower()

    # 1. Standard Django syntax validation
    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError("Please enter a valid email address.")

    if "@" not in email:
        raise ValidationError("Please enter a valid email address.")

    local_part, domain = email.rsplit("@", 1)
    local_part = local_part.strip()
    domain = domain.strip().lower()

    # 2. Check for disposable / test domains
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError(
            "Temporary or disposable email addresses are not allowed. "
            "Please use a genuine Google (@gmail.com) or personal email address."
        )

    # 3. Check domain has a valid structure: at least one period, TLD at least 2 alpha chars
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or not all(domain_parts) or len(domain_parts[-1]) < 2:
        raise ValidationError("Please enter an email with a valid domain (e.g. gmail.com).")

    if not domain_parts[-1].isalpha():
        raise ValidationError("Email domain suffix must contain valid letters (e.g. .com, .org, .et).")

    # 4. Check for obviously fake local parts
    clean_local = re.sub(r'[^a-z0-9]', '', local_part)
    if clean_local in FAKE_USERNAMES:
        raise ValidationError("Please enter your real personal or work email address.")

    # 5. Gmail / Google specific format check:
    # Google requires usernames between 6 and 30 characters, alphanumeric and non-consecutive dots
    if domain in ("gmail.com", "googlemail.com"):
        if len(local_part) < 6:
            raise ValidationError(
                "A valid Google/Gmail username must be at least 6 characters long."
            )
        if len(local_part) > 30:
            raise ValidationError(
                "A valid Google/Gmail username cannot exceed 30 characters."
            )
        if not re.match(r'^[a-z0-9]+(\.[a-z0-9]+)*$', local_part):
            raise ValidationError(
                "A valid Google/Gmail address can only contain letters, numbers, and non-consecutive dots."
            )

    return email


def validate_secure_password(password, user=None):
    """
    Enforces strong password complexity requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*...)
    - Passes Django's built-in password validators (length, common passwords, user similarity)
    """
    if not password:
        raise ValidationError("Password cannot be empty.")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter (A-Z).")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter (a-z).")

    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one number (0-9).")

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`"\'\\]', password):
        raise ValidationError(
            "Password must contain at least one special character (e.g. ! @ # $ % ^ & * _ - + =)."
        )

    # Check for predictable weak dictionary terms (case-insensitive)
    lower_pwd = password.lower()
    for weak_term in ("password", "admin", "qwerty", "letmein", "welcome", "changeme", "default", "123456"):
        if weak_term in lower_pwd:
            raise ValidationError(
                f"Password cannot contain easily guessable words like '{weak_term}'. Please choose a more unique password."
            )

    # Run Django's configured password validators (AUTH_PASSWORD_VALIDATORS in settings)
    try:
        validate_password(password, user=user)
    except ValidationError as err:
        raise ValidationError(list(err.messages))

    return password
