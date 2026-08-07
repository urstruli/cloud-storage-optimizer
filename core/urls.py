from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('project/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('project/create/', views.project_creation_view, name='project_create'),
]
