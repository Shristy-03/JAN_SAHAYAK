from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complaint/', views.complaint_view, name='complaint'),
    path('schemes/', views.schemes_view, name='schemes'),
    path('prediction/', views.prediction_dashboard, name='prediction'),
    path('get_prediction_data/', views.get_prediction_data, name='get_prediction_data'),
    path('get_city_complaints/', views.get_city_complaints, name='get_city_complaints'),
    path('logout/', views.logout_view, name='logout'),
    path('solution/', views.solution_view, name='solution'),
    path("chatbot-api/", views.chatbot_api, name="chatbot_api"),
]