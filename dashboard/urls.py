from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.UserDashboardView.as_view(), name='user_dashboard'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]