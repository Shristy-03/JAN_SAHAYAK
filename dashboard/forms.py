from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from complaints.models import Complaint
from departments.models import Department


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                widget_class = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                widget_class = 'form-select'
            else:
                widget_class = 'form-control'
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} {widget_class}".strip()


class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name', 'code', 'description', 'contact_email', 'contact_phone', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class OfficerCreateForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.none())

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already uses this email address.')
        return email

    def save(self, commit=True):
        officer = super().save(commit=False)
        officer.email = self.cleaned_data['email']
        officer.department = self.cleaned_data['department']
        officer.role = User.Role.OFFICER
        officer.email_verified = True
        if commit:
            officer.save()
        return officer


class OfficerUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'department', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already uses this email address.')
        return email


class ComplaintAssignmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ('assigned_department', 'priority')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_department'].queryset = Department.objects.filter(is_active=True)
