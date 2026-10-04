from django.urls import path

from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.CitizenComplaintListView.as_view(), name='my_complaints'),
    path('submit/', views.CitizenComplaintCreateView.as_view(), name='submit'),
    path('<str:reference_id>/', views.citizen_complaint_detail, name='detail'),
    path('<str:reference_id>/feedback/', views.submit_citizen_feedback, name='feedback'),
]
