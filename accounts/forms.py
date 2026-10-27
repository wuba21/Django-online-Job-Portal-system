from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from accounts.validators import (
    validate_google_email,
    validate_legitimate_email,
    validate_phone_number,
    validate_secure_password,
)

GENDER_CHOICES = (("male", "Male"), ("female", "Female"))


class EmployeeRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=True, label="Gender")
    phone_number = forms.CharField(
        required=True,
        label="Phone Number",
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={"placeholder": "+251 9XX XXX XXX or 09XXXXXXXX"}),
    )
    email = forms.EmailField(required=True, label="Google Email Address")

    def __init__(self, *args, **kwargs):
        super(EmployeeRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter First Name (e.g. Abebe)"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Last Name (e.g. Kebede)"})
        self.fields["gender"].widget.attrs.update({"class": "form-control"})
        self.fields["phone_number"].widget.attrs.update({"class": "form-control", "placeholder": "+251 9XX XXX XXX or 09XXXXXXXX"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Google email (e.g. yourname@gmail.com)"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Enter strong password (min 8 chars, A-Z, 0-9, symbol)"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirm password"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "gender", "phone_number", "email", "password1", "password2"]
        error_messages = {
            "first_name": {"required": "First name is required", "max_length": "Name is too long"},
            "last_name": {"required": "Last name is required", "max_length": "Last Name is too long"},
            "gender": {"required": "Gender is required"},
            "phone_number": {"required": "Phone number is required"},
            "email": {"required": "Email is required", "invalid": "Enter a valid email address"},
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        validate_google_email(email)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this Google email already exists. Please log in.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_secure_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def clean_gender(self):
        gender = self.cleaned_data.get("gender")
        if not gender:
            raise forms.ValidationError("Gender is required")
        return gender

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "").strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        user.gender = self.cleaned_data.get("gender")
        user.phone_number = self.cleaned_data.get("phone_number", "").strip()
        user.email = self.cleaned_data.get("email").strip().lower()
        user.role = "employee"
        user.is_active = True
        if commit:
            user.save()
        return user


class EmployerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="Contact Person First Name")
    last_name = forms.CharField(required=True, label="Contact Person Last Name")
    company_name = forms.CharField(required=True, label="Company / Organization Name")
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=True, label="Gender")
    phone_number = forms.CharField(
        required=True,
        label="Phone Number",
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={"placeholder": "+251 9XX XXX XXX or 09XXXXXXXX"}),
    )
    email = forms.EmailField(required=True, label="Company Google Email")

    def __init__(self, *args, **kwargs):
        super(EmployerRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Contact Person First Name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Contact Person Last Name"})
        self.fields["company_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Company Name (e.g. Awash Bank, Ethio Tech)"})
        self.fields["gender"].widget.attrs.update({"class": "form-control"})
        self.fields["phone_number"].widget.attrs.update({"class": "form-control", "placeholder": "+251 9XX XXX XXX or 09XXXXXXXX"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Company Google email (e.g. company@gmail.com)"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Enter strong password (min 8 chars, A-Z, 0-9, symbol)"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirm password"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "company_name", "gender", "phone_number", "email", "password1", "password2"]
        error_messages = {
            "first_name": {"required": "Contact person first name is required", "max_length": "First name is too long"},
            "last_name": {"required": "Contact person last name is required", "max_length": "Last name is too long"},
            "company_name": {"required": "Company name is required", "max_length": "Company name is too long"},
            "gender": {"required": "Gender is required"},
            "phone_number": {"required": "Phone number is required"},
            "email": {"required": "Email is required", "invalid": "Enter a valid email address"},
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        validate_google_email(email)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An employer account with this Google email already exists. Please log in.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_secure_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def clean_gender(self):
        gender = self.cleaned_data.get("gender")
        if not gender:
            raise forms.ValidationError("Gender is required")
        return gender

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "").strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        user.gender = self.cleaned_data.get("gender")
        user.phone_number = self.cleaned_data.get("phone_number", "").strip()
        user.email = self.cleaned_data.get("email").strip().lower()
        user.role = "employer"
        user.is_active = True
        if commit:
            user.save()
            company_name = self.cleaned_data.get("company_name", "").strip() or f"{user.first_name}'s Company"
            from accounts.models import Company
            Company.objects.update_or_create(user=user, defaults={"name": company_name})
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(label="Google Email Address")
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your Google email (e.g. name@gmail.com)",
            "autocomplete": "email",
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your password",
            "autocomplete": "current-password",
        })

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            email = email.strip().lower()
            user_obj = User.objects.filter(email__iexact=email).first()
            if user_obj is None:
                raise forms.ValidationError("No account found with this email address.")

            if not user_obj.is_active:
                raise forms.ValidationError("This user account is inactive. Please contact support.")

            self.user = authenticate(email=user_obj.email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid password. Please check your password and try again.")

        return super(UserLoginForm, self).clean(*args, **kwargs)

    def get_user(self):
        return self.user


class EmployeeProfileUpdateForm(forms.ModelForm):
    GENDER_CHOICES = [
        ("", "Select Gender"),
        ("male", "Male"),
        ("female", "Female"),
    ]
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super(EmployeeProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter First Name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Last Name"})
        if "phone_number" in self.fields:
            self.fields["phone_number"].widget.attrs.update({"class": "form-control", "placeholder": "+251 9..."})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "gender", "phone_number"]


class EmployerProfileUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EmployerProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter First Name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Enter Last Name"})
        if "phone_number" in self.fields:
            self.fields["phone_number"].widget.attrs.update({"class": "form-control", "placeholder": "+251 9..."})
        self.fields["first_name"].label = "Contact Person First Name"
        self.fields["last_name"].label = "Contact Person Last Name"

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number"]
