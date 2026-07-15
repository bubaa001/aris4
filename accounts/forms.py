from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ParentChildLink

# ---------- REGISTRATION FORM ----------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'})
    )
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.RadioSelect()
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'w-full border border-gray-300 rounded p-2'})

# ---------- LOGIN FORM ----------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded p-2', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full border border-gray-300 rounded p-2', 'placeholder': 'Password'})
    )


# ---------- PARENT REGISTRATION FORM ----------
class ParentRegisterForm(UserCreationForm):
    """Simpler registration for parents — no role selection needed."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'w-full border border-gray-300 rounded p-2'})