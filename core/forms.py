from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Complaint


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['problem', 'state', 'city', 'area','pincode', 'description']
        widgets = {
            'state': forms.Select(attrs={'id': 'state'}),
            'city': forms.Select(attrs={'id': 'city'}),
            'area': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 200,
                'placeholder': 'Enter your area'
            }),
            'pincode': forms.TextInput(attrs={'placeholder': 'Enter Pincode'}),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'maxlength': 2000,
                'placeholder': 'Describe your problem (max 300 words)'
            }),
        }
