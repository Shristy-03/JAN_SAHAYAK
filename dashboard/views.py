from datetime import timedelta
import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from accounts.decorators import administrator_required
from accounts.models import User
from complaints.models import Complaint, ComplaintCategory, Feedback
from departments.models import Department

from .forms import ComplaintAssignmentForm, DepartmentForm, OfficerCreateForm, OfficerUpdateForm
from .services import assign_complaint, queue_overdue_notification


def all_complaints():
    return Complaint.objects.select_related('citizen', 'category', 'assigned_department')


@method_decorator(administrator_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaints = Complaint.objects.all()
        context['totals'] = complaints.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=Complaint.Status.PENDING)),
            in_progress=Count('id', filter=Q(status=Complaint.Status.IN_PROGRESS)),
            completed=Count('id', filter=Q(status=Complaint.Status.COMPLETED)),
            rejected=Count('id', filter=Q(status=Complaint.Status.REJECTED)),
        )
        context['citizen_count'] = User.objects.filter(role=User.Role.CITIZEN).count()
        context['department_count'] = Department.objects.count()
        context['overdue_count'] = complaints.overdue().count()
        context['recent_complaints'] = all_complaints()[:8]
        context['category_summary'] = list(
            complaints.values('category__name').annotate(total=Count('id')).order_by('-total', 'category__name')
        )
        performance = Department.objects.annotate(
            total=Count('complaints'),
            completed=Count('complaints', filter=Q(complaints__status=Complaint.Status.COMPLETED)),
            overdue=Count(
                'complaints',
                filter=Q(complaints__expected_resolution_at__lt=timezone.now()) & ~Q(complaints__status__in=[Complaint.Status.COMPLETED, Complaint.Status.REJECTED]),
            ),
        ).order_by('name')
        context['department_performance'] = [
            {
                'name': department.name,
                'total': department.total,
                'completed': department.completed,
                'overdue': department.overdue,
                'completion_rate': round((department.completed / department.total) * 100) if department.total else 0,
            }
            for department in performance
        ]
        start_date = timezone.localdate() - timedelta(days=6)
        context['trend'] = list(
            complaints.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Count('id'))
            .order_by('day')
        )
        status_counts = {
            Complaint.Status.PENDING: context['totals']['pending'],
            Complaint.Status.IN_PROGRESS: context['totals']['in_progress'],
            Complaint.Status.COMPLETED: context['totals']['completed'],
            Complaint.Status.REJECTED: context['totals']['rejected'],
        }
        trend_by_day = {item['day'].isoformat(): item['total'] for item in context['trend']}
        chart_days = [start_date + timedelta(days=offset) for offset in range(7)]
        context['chart_data'] = {
            'status': {
                'labels': [label for _, label in Complaint.Status.choices],
                'values': [status_counts[value] for value, _ in Complaint.Status.choices],
            },
            'category': {
                'labels': [item['category__name'] for item in context['category_summary']],
                'values': [item['total'] for item in context['category_summary']],
            },
            'trend': {
                'labels': [day.strftime('%d %b') for day in chart_days],
                'values': [trend_by_day.get(day.isoformat(), 0) for day in chart_days],
            },
            'department_performance': {
                'labels': [item['name'] for item in context['department_performance']],
                'values': [item['completion_rate'] for item in context['department_performance']],
            },
        }
        context['chart_data_json'] = json.dumps(context['chart_data'])
        return context


@method_decorator(administrator_required, name='dispatch')
class AdminComplaintListView(ListView):
    template_name = 'dashboard/complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 25

    def get_queryset(self):
        queryset = all_complaints()
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        department = self.request.GET.get('department')
        valid_statuses = {choice[0] for choice in Complaint.Status.choices}
        if status in valid_statuses:
            queryset = queryset.filter(status=status)
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)
        if department and department.isdigit():
            queryset = queryset.filter(assigned_department_id=department)
        if self.request.GET.get('overdue') == '1':
            queryset = queryset.overdue()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ComplaintCategory.objects.filter(is_active=True)
        context['departments'] = Department.objects.filter(is_active=True)
        context['status_choices'] = Complaint.Status.choices
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'department': self.request.GET.get('department', ''),
            'overdue': self.request.GET.get('overdue', ''),
        }
        return context


@administrator_required
def admin_complaint_detail(request, reference_id):
    complaint = get_object_or_404(
        all_complaints().prefetch_related('images', 'resolution_proofs', 'status_history__changed_by', 'updates__author'),
        reference_id=reference_id,
    )
    return render(request, 'dashboard/complaint_detail.html', {
        'complaint': complaint,
        'assignment_form': ComplaintAssignmentForm(instance=complaint),
        'feedback': getattr(complaint, 'feedback', None),
    })


@administrator_required
@require_POST
def admin_complaint_assign(request, reference_id):
    complaint = get_object_or_404(all_complaints(), reference_id=reference_id)
    form = ComplaintAssignmentForm(request.POST, instance=complaint)
    if form.is_valid():
        assign_complaint(
            complaint=complaint,
            department=form.cleaned_data['assigned_department'],
            priority=form.cleaned_data['priority'],
            actor=request.user,
        )
        messages.success(request, 'Complaint assignment was updated.')
        return redirect('dashboard:complaint_detail', reference_id=complaint.reference_id)
    return render(request, 'dashboard/complaint_detail.html', {
        'complaint': complaint,
        'assignment_form': form,
        'feedback': getattr(complaint, 'feedback', None),
    }, status=400)


@administrator_required
@require_POST
def notify_overdue(request, reference_id):
    complaint = get_object_or_404(all_complaints(), reference_id=reference_id)
    try:
        count = queue_overdue_notification(complaint=complaint)
    except ValidationError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f'Urgency notification queued for {count} department officer(s).')
    return redirect('dashboard:complaint_detail', reference_id=complaint.reference_id)


@method_decorator(administrator_required, name='dispatch')
class DepartmentListView(ListView):
    template_name = 'dashboard/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.annotate(officer_count=Count('officers'), complaint_count=Count('complaints')).order_by('name')


@method_decorator(administrator_required, name='dispatch')
class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'dashboard/department_form.html'
    success_url = reverse_lazy('dashboard:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department created.')
        return super().form_valid(form)


@method_decorator(administrator_required, name='dispatch')
class DepartmentUpdateView(UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'dashboard/department_form.html'
    success_url = reverse_lazy('dashboard:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department updated.')
        return super().form_valid(form)


@method_decorator(administrator_required, name='dispatch')
class OfficerListView(ListView):
    template_name = 'dashboard/officer_list.html'
    context_object_name = 'officers'
    paginate_by = 25

    def get_queryset(self):
        return User.objects.filter(role=User.Role.OFFICER).select_related('department').order_by('department__name', 'username')


@method_decorator(administrator_required, name='dispatch')
class OfficerCreateView(CreateView):
    form_class = OfficerCreateForm
    template_name = 'dashboard/officer_form.html'
    success_url = reverse_lazy('dashboard:officer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department officer account created.')
        return super().form_valid(form)


@method_decorator(administrator_required, name='dispatch')
class OfficerUpdateView(UpdateView):
    model = User
    form_class = OfficerUpdateForm
    template_name = 'dashboard/officer_form.html'
    success_url = reverse_lazy('dashboard:officer_list')

    def get_queryset(self):
        return User.objects.filter(role=User.Role.OFFICER)

    def form_valid(self, form):
        messages.success(self.request, 'Department officer updated.')
        return super().form_valid(form)


@method_decorator(administrator_required, name='dispatch')
class FeedbackListView(ListView):
    template_name = 'dashboard/feedback_list.html'
    context_object_name = 'feedback_entries'
    paginate_by = 25

    def get_queryset(self):
        return Feedback.objects.select_related('citizen', 'complaint__category', 'complaint__assigned_department')
