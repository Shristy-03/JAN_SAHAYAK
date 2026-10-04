from decimal import Decimal

from django import forms
from PIL import Image

from .models import Complaint, ComplaintCategory, Feedback


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGES_PER_COMPLAINT = 5
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def validate_image_file(uploaded_file):
    """Validate image content, type, and size before it reaches media storage."""
    if uploaded_file.size > MAX_IMAGE_SIZE_BYTES:
        raise forms.ValidationError('Each image must be 5 MB or smaller.')
    try:
        image = Image.open(uploaded_file)
        image.verify()
        if image.format not in ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError('Upload a JPEG, PNG, or WebP image.')
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as error:
        raise forms.ValidationError('Upload a valid JPEG, PNG, or WebP image.') from error
    finally:
        uploaded_file.seek(0)
    return uploaded_file


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [uploaded_file for uploaded_file in files if uploaded_file]
        if len(files) > MAX_IMAGES_PER_COMPLAINT:
            raise forms.ValidationError(f'Upload no more than {MAX_IMAGES_PER_COMPLAINT} images.')
        return [validate_image_file(uploaded_file) for uploaded_file in files]


class ComplaintCreateForm(forms.ModelForm):
    """Citizen-facing form for submitting a new civic issue."""

    images = MultipleImageField(required=False, widget=MultipleImageInput(attrs={
        'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp', 'multiple': True,
    }))
    latitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}))
    longitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}))

    class Meta:
        model = Complaint
        fields = ('category', 'title', 'description', 'location_text')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Briefly describe the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Include relevant details that will help the department resolve it.'}),
            'location_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address, landmark, or area (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ComplaintCategory.objects.filter(is_active=True).order_by('name')
        self.fields['category'].empty_label = 'Choose a category'

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_description(self):
        return self.cleaned_data['description'].strip()

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError('Provide both latitude and longitude, or leave both empty.')
        if latitude is not None and not Decimal('-90') <= latitude <= Decimal('90'):
            self.add_error('latitude', 'Latitude must be between -90 and 90.')
        if longitude is not None and not Decimal('-180') <= longitude <= Decimal('180'):
            self.add_error('longitude', 'Longitude must be between -180 and 180.')
        return cleaned_data


class ResolutionProofUploadForm(forms.Form):
    image = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp',
    }))
    description = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Brief description of the completed work',
    }))

    def clean_image(self):
        return validate_image_file(self.cleaned_data['image'])


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(choices=[('', 'Choose a rating')] + [(rating, f'{rating} / 5') for rating in range(1, 6)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about the resolution (optional).'}),
        }
