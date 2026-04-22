from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UploadCSVForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}))


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('password')
        pw2 = cleaned.get('password_confirm')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya existe.')
        return username


class UserEditForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password_confirm = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('new_password')
        pw2 = cleaned.get('new_password_confirm')
        if pw1 and pw1 != pw2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('new_password')
        pw2 = cleaned.get('new_password_confirm')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned
