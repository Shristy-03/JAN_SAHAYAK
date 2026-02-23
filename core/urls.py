from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complaint/', views.complaint_view, name='complaint'),
    path('schemes/', views.schemes_view, name='schemes'),
    path('prediction/', views.prediction_view, name='prediction'),
    path('logout/', views.logout_view, name='logout'),
]
