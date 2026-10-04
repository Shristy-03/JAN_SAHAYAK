from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('complaints/', views.AdminComplaintListView.as_view(), name='complaint_list'),
    path('complaints/<str:reference_id>/', views.admin_complaint_detail, name='complaint_detail'),
    path('complaints/<str:reference_id>/assign/', views.admin_complaint_assign, name='complaint_assign'),
    path('complaints/<str:reference_id>/notify-overdue/', views.notify_overdue, name='notify_overdue'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_add'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('officers/', views.OfficerListView.as_view(), name='officer_list'),
    path('officers/add/', views.OfficerCreateView.as_view(), name='officer_add'),
    path('officers/<int:pk>/edit/', views.OfficerUpdateView.as_view(), name='officer_edit'),
    path('feedback/', views.FeedbackListView.as_view(), name='feedback_list'),
]
