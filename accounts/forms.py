from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from accounts.validators import validate_legitimate_email, validate_secure_password

GENDER_CHOICES = (("male", "Male"), ("female", "Female"))


class EmployeeRegistrationForm(UserCreationForm):
    # gender = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=GENDER_CHOICES)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(EmployeeRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["gender"].required = True
        self.fields["first_name"].label = "First Name"
        self.fields["last_name"].label = "Last Name"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm Password"

        self.fields["first_name"].widget.attrs.update({"placeholder": "Enter First Name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Enter Last Name"})
        self.fields["email"].widget.attrs.update({"placeholder": "Enter valid email (e.g. name@gmail.com)"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Enter strong password (min 8 chars, A-Z, 0-9, symbol)"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm password"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2", "gender"]
        error_messages = {
            "first_name": {"required": "First name is required", "max_length": "Name is too long"},
            "last_name": {"required": "Last name is required", "max_length": "Last Name is too long"},
            "gender": {"required": "Gender is required"},
            "email": {"required": "Email is required", "invalid": "Enter a valid email address"},
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        validate_legitimate_email(email)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists. Please login instead.")
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
        user.email = self.cleaned_data.get("email").strip().lower()
        user.role = "employee"
        if commit:
            user.save()
        return user


class EmployerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(EmployerRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].label = "Company Name"
        self.fields["last_name"].label = "Company Address"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm Password"

        self.fields["first_name"].widget.attrs.update({"placeholder": "Enter Company Name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Enter Company Address"})
        self.fields["email"].widget.attrs.update({"placeholder": "Enter valid email (e.g. company@gmail.com)"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Enter strong password (min 8 chars, A-Z, 0-9, symbol)"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm password"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]
        error_messages = {
            "first_name": {"required": "Company name is required", "max_length": "Company Name is too long"},
            "last_name": {"required": "Company address is required", "max_length": "Company Address is too long"},
            "email": {"required": "Email is required", "invalid": "Enter a valid email address"},
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        validate_legitimate_email(email)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An employer account with this email address already exists. Please login.")
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

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data.get("email").strip().lower()
        user.role = "employer"
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields["email"].widget.attrs.update({"placeholder": "Enter Email"})
        self.fields["password"].widget.attrs.update({"placeholder": "Enter Password"})

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
