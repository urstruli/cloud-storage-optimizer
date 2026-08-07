from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Permission, Project


def requires_role(required_role):
    """
    Decorator to check if user has a specific role in a project.
    Usage: @requires_role('Admin')
    
    No global variables — all data passed as parameters.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in.')
                return redirect('login')
            
            # Get project_id from URL kwargs
            project_id = kwargs.get('project_id')
            if not project_id:
                messages.error(request, 'Project not found.')
                return redirect('dashboard')
            
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                messages.error(request, 'Project does not exist.')
                return redirect('dashboard')
            
            # Check if user is the owner (owners always have full access)
            if project.owner == request.user:
                return view_func(request, *args, **kwargs)
            
            # Check if user has the required role via Permission
            try:
                permission = Permission.objects.get(
                    user=request.user,
                    project=project
                )
                if permission.role.name == required_role:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'You need {required_role} role to access this.')
                    return redirect('dashboard')
            except Permission.DoesNotExist:
                messages.error(request, 'You do not have access to this project.')
                return redirect('dashboard')
        
        return wrapper
    return decorator


def requires_project_permission(view_func):
    """
    Decorator to check if user has ANY permission on a project.
    Allows access if user is owner or has explicit permission.
    
    Usage: @requires_project_permission
    
    No global variables — all data passed as parameters.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in.')
            return redirect('login')
        
        # Get project_id from URL kwargs
        project_id = kwargs.get('project_id')
        if not project_id:
            messages.error(request, 'Project not found.')
            return redirect('dashboard')
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            messages.error(request, 'Project does not exist.')
            return redirect('dashboard')
        
        # Owner always has access
        if project.owner == request.user:
            return view_func(request, *args, **kwargs)
        
        # Check if user has any permission on this project
        has_permission = Permission.objects.filter(
            user=request.user,
            project=project
        ).exists()
        
        if has_permission:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'You do not have access to this project.')
            return redirect('dashboard')
    
    return wrapper