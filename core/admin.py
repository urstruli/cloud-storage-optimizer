from django.contrib import admin
from .models import Role, Project, File, Permission, CostLog, AuditLog, Recommendation


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'owner', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('project_name',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'file_size', 'is_duplicate', 'is_stale')
    list_filter = ('project', 'is_duplicate', 'is_stale')
    search_fields = ('file_name', 's3_key')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'granted_at')
    list_filter = ('role', 'granted_at')
    search_fields = ('user__username', 'project__project_name')


@admin.register(CostLog)
class CostLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'total_size_bytes', 'monthly_cost', 'recorded_at')
    list_filter = ('project', 'recorded_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource_type', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('user__username', 'action')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('project', 'recommendation_type', 'potential_savings', 'created_at')
    list_filter = ('recommendation_type', 'created_at')