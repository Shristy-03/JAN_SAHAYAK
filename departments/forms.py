from django import forms

from complaints.models import Complaint


class DepartmentComplaintUpdateForm(forms.Form):
    """An officer update to the state, priority, or public progress note."""

    status = forms.ChoiceField(choices=Complaint.Status.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    priority = forms.ChoiceField(choices=Complaint.Priority.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Add a progress update or reason for this change.'}),
    )
    citizen_visible = forms.BooleanField(required=False, initial=True, label='Show this note to the citizen')

    def __init__(self, *args, complaint: Complaint, **kwargs):
        self.complaint = complaint
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = complaint.status
        self.fields['priority'].initial = complaint.priority
        if not complaint.resolution_proofs.exists():
            self.fields['status'].choices = [
                choice for choice in Complaint.Status.choices if choice[0] != Complaint.Status.COMPLETED
            ]

    def clean_status(self):
        status = self.cleaned_data['status']
        if status == Complaint.Status.COMPLETED and not self.complaint.resolution_proofs.exists():
            raise forms.ValidationError('Upload at least one resolution proof image before completing this complaint.')
        return status

    def clean_note(self):
        return self.cleaned_data['note'].strip()
