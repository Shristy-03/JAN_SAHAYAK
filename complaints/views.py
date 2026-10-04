from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from accounts.decorators import citizen_required

from .forms import ComplaintCreateForm, FeedbackForm
from .models import Complaint
from .services import submit_complaint, submit_feedback


@method_decorator(citizen_required, name='dispatch')
class CitizenComplaintCreateView(CreateView):
    form_class = ComplaintCreateForm
    template_name = 'complaints/complaint_form.html'

    def form_valid(self, form):
        self.object = submit_complaint(
            citizen=self.request.user,
            category=form.cleaned_data['category'],
            title=form.cleaned_data['title'],
            description=form.cleaned_data['description'],
            location_text=form.cleaned_data['location_text'],
            latitude=form.cleaned_data['latitude'],
            longitude=form.cleaned_data['longitude'],
            images=form.cleaned_data['images'],
        )
        messages.success(self.request, f'Complaint {self.object.reference_id} was submitted successfully.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('complaints:detail', kwargs={'reference_id': self.object.reference_id})


@method_decorator(citizen_required, name='dispatch')
class CitizenComplaintListView(ListView):
    template_name = 'complaints/complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 15

    def get_queryset(self):
        queryset = Complaint.objects.filter(citizen=self.request.user).select_related('category', 'assigned_department')
        selected_status = self.request.GET.get('status')
        valid_statuses = {choice[0] for choice in Complaint.Status.choices}
        if selected_status in valid_statuses:
            queryset = queryset.filter(status=selected_status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['totals'] = Complaint.objects.filter(citizen=self.request.user).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=Complaint.Status.PENDING)),
            in_progress=Count('id', filter=Q(status=Complaint.Status.IN_PROGRESS)),
            completed=Count('id', filter=Q(status=Complaint.Status.COMPLETED)),
        )
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Complaint.Status.choices
        return context


@citizen_required
def citizen_complaint_detail(request, reference_id, feedback_form=None):
    """Display one complaint only when it belongs to the signed-in citizen."""
    complaint = get_object_or_404(
        Complaint.objects.select_related('category', 'assigned_department').prefetch_related('images', 'resolution_proofs', 'status_history__changed_by', 'updates__author'),
        reference_id=reference_id,
        citizen=request.user,
    )
    feedback = getattr(complaint, 'feedback', None)
    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'feedback': feedback,
        'feedback_form': feedback_form or FeedbackForm(),
    })


@citizen_required
@require_POST
def submit_citizen_feedback(request, reference_id):
    complaint = get_object_or_404(Complaint, reference_id=reference_id, citizen=request.user)
    form = FeedbackForm(request.POST)
    if form.is_valid():
        try:
            submit_feedback(complaint=complaint, citizen=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error.message)
        else:
            messages.success(request, 'Thank you for your feedback.')
            return redirect('complaints:detail', reference_id=complaint.reference_id)
    return citizen_complaint_detail(request, reference_id, feedback_form=form)
