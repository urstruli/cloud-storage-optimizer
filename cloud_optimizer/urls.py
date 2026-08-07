from django.contrib import admin
from django.urls import path
from core.views import login_view, dashboard_view, logout_view, project_detail_view, project_creation_view, s3_inventory_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('', login_view, name='home'),
    path('project/<int:project_id>/', project_detail_view, name='project_detail'),
    path('project/create/', project_creation_view, name='project_create'),
    path('inventory/', s3_inventory_view, name='s3_inventory'),
]