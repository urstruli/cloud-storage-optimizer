from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Sum

from .models import Project, Permission, File, Role, AuditLog
from .forms import CustomAuthenticationForm, ProjectCreationForm
from .permissions import requires_project_permission
from .models import Project, Permission, File, Role, AuditLog, CostLog

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Handle user login. GET shows form, POST processes login.
    No global variables—all data passed as parameters.
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'core/login.html', {'form': form})

@require_http_methods(["POST"])
@login_required(login_url='login')
def logout_view(request):
    """
    Handle user logout.
    """
    user_name = request.user.username
    logout(request)
    messages.success(request, f'You have been logged out. Goodbye, {user_name}!')
    return redirect('login')

@require_http_methods(["GET"])
@login_required(login_url='login')
def dashboard_view(request):
    """
    Display dashboard for logged-in user.
    Shows projects they own or have access to.
    Calculates: total storage used, estimated cost, project count, file count.
    No global variables-all data passed as parameters.
    """
    user = request.user
    owned_projects = Project.objects.filter(owner=user)
    accessible_projects = Permission.objects.filter(user=user).select_related('project')

    # Get all project IDs user can access (owned + permissioned)
    accessible_project_ids = list(owned_projects.values_list('id', flat=True))
    permissioned_project_ids = list(Permission.objects.filter(user=user).values_list('project_id', flat=True))
    all_project_ids = set(list(accessible_project_ids) + permissioned_project_ids)

    # Calculate total storage used across all projects user can access
    total_storage_bytes = File.objects.filter(project_id__in=all_project_ids).aggregate(Sum('file_size'))['file_size__sum'] or 0
    total_storage_gb = total_storage_bytes / (1024 ** 3)  # Convert bytes to GB

    # Estimate monthly cost ($0.023 per GB per AWS S3 standard pricing)
    estimated_monthly_cost = total_storage_gb * 0.023

    # Count projects and files
    total_projects = len(all_project_ids)
    total_files = File.objects.filter(project_id__in=all_project_ids).count()

    # Get recent audit logs (last 10)
    recent_audit_logs = AuditLog.objects.all().order_by('-created_at')[:10]
    recent_cost_logs = CostLog.objects.all().order_by('-recorded_at')[:10]

    context = {
        'owned_projects': owned_projects,
        'accessible_projects': accessible_projects,
        'total_storage_gb': round(total_storage_gb, 2),
        'estimated_monthly_cost': round(estimated_monthly_cost, 2),
        'total_projects': total_projects,
        'total_files': total_files,
        'audit_logs': recent_audit_logs,
        'cost_logs': recent_cost_logs,
    }
    return render(request, 'core/dashboard.html', context)

@require_http_methods(["GET"])
@login_required(login_url='login')
@requires_project_permission
def project_detail_view(request, project_id):
    """
    Display project details. Protected by @requires_project_permission.
    Only owner or users with explicit permission can view.
    Includes: project info, files, team members, storage stats.
    """

    project = Project.objects.get(id=project_id)
    permissions = Permission.objects.filter(project=project).select_related('user', 'role')
    
    # Get files in this project
    files = File.objects.filter(project=project).order_by('-created_at')
    
    # Calculate project-specific storage stats
    project_storage_bytes = files.aggregate(Sum('file_size'))['file_size__sum'] or 0
    project_storage_gb = round(project_storage_bytes / (1024 ** 3), 2)
    
    # Estimate monthly cost for this project ($0.023 per GB per month AWS S3 standard pricing)
    project_estimated_cost = round(project_storage_gb * 0.023, 2)
    
    # File count
    file_count = files.count()

    context = {
        'project': project,
        'permissions': permissions,
        'files': files,
        'project_storage_gb': project_storage_gb,
        'project_estimated_cost': project_estimated_cost,
        'file_count': file_count,
    }
    
    return render(request, 'core/project_detail.html', context)

@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def project_creation_view(request):
    """
    Handle project creation. GET shows form, POST processes creation.
    Auto-assigns creator as Admin via Permission model.
    No global variables—all data passed as parameters.
    """
    if request.method == 'POST':
        form = ProjectCreationForm(request.user, request.POST)
        if form.is_valid():
            project_name = form.cleaned_data.get('project_name')
            description = form.cleaned_data.get('description')
            
            # Create project with current user as owner
            project = Project.objects.create(
                project_name=project_name,
                description=description,
                owner=request.user
            )
            
            # Auto-assign creator as Admin
            admin_role = Role.objects.get(name='Admin')
            Permission.objects.create(
                user=request.user,
                project=project,
                role=admin_role
            )
            
            messages.success(request, f'Project "{project_name}" created successfully!')
            return redirect('project_detail', project_id=project.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ProjectCreationForm(request.user)
    
    context = {'form': form}
    return render(request, 'core/project_creation.html', context)

@require_http_methods(["GET"])
@login_required(login_url='login')
def s3_inventory_view(request):
    """
    Display S3 Inventory files ingested from mock data.
    Shows all files, duplicates, and stale files.
    """
    
    # Get all files, ordered by file size (largest first)
    all_files = File.objects.all().order_by('-file_size')
    duplicate_files = all_files.filter(is_duplicate=True)
    stale_files = all_files.filter(is_stale=True)
    
    # Calculate total storage
    from django.db.models import Sum
    total_storage_bytes = all_files.aggregate(Sum('file_size'))['file_size__sum'] or 0
    total_storage_gb = round(total_storage_bytes / (1024 ** 3), 2)
    
    # Calculate duplicate storage (wasted space)
    duplicate_storage_bytes = duplicate_files.aggregate(Sum('file_size'))['file_size__sum'] or 0
    duplicate_storage_gb = round(duplicate_storage_bytes / (1024 ** 3), 2)
    
    # Calculate stale storage
    stale_storage_bytes = stale_files.aggregate(Sum('file_size'))['file_size__sum'] or 0
    stale_storage_gb = round(stale_storage_bytes / (1024 ** 3), 2)
    
    # Count files
    total_file_count = all_files.count()
    
    context = {
        'files': all_files,
        'duplicate_files': duplicate_files,
        'stale_files': stale_files,
        'total_storage_gb': total_storage_gb,
        'duplicate_storage_gb': duplicate_storage_gb,
        'stale_storage_gb': stale_storage_gb,
        'total_file_count': total_file_count,
        'duplicate_count': duplicate_files.count(),
        'stale_count': stale_files.count(),
    }
    
    return render(request, 'core/s3_inventory.html', context)