from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from accounts.decorators import department_officer_required
from complaints.forms import ResolutionProofUploadForm
from complaints.models import Complaint, ResolutionProof

from .forms import DepartmentComplaintUpdateForm
from .services import update_department_complaint


def department_complaints_for(user):
    return Complaint.objects.assigned_to_department(user.department).select_related('citizen', 'category', 'assigned_department')


@method_decorator(department_officer_required, name='dispatch')
class DepartmentDashboardView(TemplateView):
    template_name = 'departments/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaints = department_complaints_for(self.request.user)
        context['department'] = self.request.user.department
        context['totals'] = complaints.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=Complaint.Status.PENDING)),
            in_progress=Count('id', filter=Q(status=Complaint.Status.IN_PROGRESS)),
            completed=Count('id', filter=Q(status=Complaint.Status.COMPLETED)),
        )
        context['overdue_count'] = complaints.overdue().count()
        context['recent_complaints'] = complaints[:6]
        return context


@method_decorator(department_officer_required, name='dispatch')
class DepartmentComplaintListView(ListView):
    template_name = 'departments/complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 20

    def get_queryset(self):
        queryset = department_complaints_for(self.request.user)
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        start_date = parse_date(self.request.GET.get('start_date', ''))
        end_date = parse_date(self.request.GET.get('end_date', ''))
        valid_statuses = {choice[0] for choice in Complaint.Status.choices}
        if status in valid_statuses:
            queryset = queryset.filter(status=status)
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department_complaints = department_complaints_for(self.request.user)
        context['categories'] = department_complaints.order_by('category__name').values_list('category__id', 'category__name').distinct()
        context['status_choices'] = Complaint.Status.choices
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
        }
        return context


@department_officer_required
def department_complaint_detail(request, reference_id):
    complaint = get_object_or_404(
        department_complaints_for(request.user).prefetch_related('images', 'resolution_proofs', 'status_history__changed_by', 'updates__author'),
        reference_id=reference_id,
    )
    feedback = getattr(complaint, 'feedback', None)
    update_form = DepartmentComplaintUpdateForm(complaint=complaint)
    return render(request, 'departments/complaint_detail.html', {
        'complaint': complaint,
        'feedback': feedback,
        'update_form': update_form,
        'proof_form': ResolutionProofUploadForm(),
    })


@department_officer_required
@require_POST
def department_complaint_update(request, reference_id):
    complaint = get_object_or_404(department_complaints_for(request.user), reference_id=reference_id)
    form = DepartmentComplaintUpdateForm(request.POST, complaint=complaint)
    if form.is_valid():
        try:
            update_department_complaint(complaint=complaint, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error.message)
        else:
            messages.success(request, 'Complaint update saved.')
            return redirect('departments:complaint_detail', reference_id=complaint.reference_id)
    feedback = getattr(complaint, 'feedback', None)
    return render(request, 'departments/complaint_detail.html', {
        'complaint': complaint,
        'feedback': feedback,
        'update_form': form,
        'proof_form': ResolutionProofUploadForm(),
    }, status=400)


@department_officer_required
@require_POST
def upload_resolution_proof(request, reference_id):
    complaint = get_object_or_404(department_complaints_for(request.user), reference_id=reference_id)
    form = ResolutionProofUploadForm(request.POST, request.FILES)
    if form.is_valid():
        ResolutionProof.objects.create(
            complaint=complaint,
            image=form.cleaned_data['image'],
            description=form.cleaned_data['description'],
            uploaded_by=request.user,
        )
        messages.success(request, 'Resolution proof uploaded. You can now mark the complaint completed.')
        return redirect('departments:complaint_detail', reference_id=complaint.reference_id)
    feedback = getattr(complaint, 'feedback', None)
    return render(request, 'departments/complaint_detail.html', {
        'complaint': complaint,
        'feedback': feedback,
        'update_form': DepartmentComplaintUpdateForm(complaint=complaint),
        'proof_form': form,
    }, status=400)
