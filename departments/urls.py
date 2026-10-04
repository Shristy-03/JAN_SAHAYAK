from django.urls import path

from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.DepartmentDashboardView.as_view(), name='dashboard'),
    path('complaints/', views.DepartmentComplaintListView.as_view(), name='complaint_list'),
    path('complaints/<str:reference_id>/', views.department_complaint_detail, name='complaint_detail'),
    path('complaints/<str:reference_id>/update/', views.department_complaint_update, name='complaint_update'),
    path('complaints/<str:reference_id>/resolution-proof/', views.upload_resolution_proof, name='resolution_proof_upload'),
]
