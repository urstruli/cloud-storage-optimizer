from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Role(models.Model):
    """
    Defines roles in the system: Admin, Editor, Viewer.
    Maps to core_role table.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'core_role'


class Project(models.Model):
    """
    Stores projects owned by users. Each project contains files.
    Maps to core_project table.
    """
    project_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.project_name

    class Meta:
        db_table = 'core_project'
        indexes = [
            models.Index(fields=['owner']),
        ]


class File(models.Model):
    """
    Stores file metadata from S3 Inventory. Each file belongs to a project.
    Maps to core_file table.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    s3_key = models.CharField(max_length=1024)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(validators=[MinValueValidator(0)])
    storage_class = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(blank=True, null=True)
    is_duplicate = models.BooleanField(default=False)
    is_stale = models.BooleanField(default=False)

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = 'core_file'
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['is_duplicate']),
            models.Index(fields=['is_stale']),
        ]


class Permission(models.Model):
    """
    Maps users to projects with specific roles (role-based access control).
    Maps to core_permission table.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_permissions')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='permissions')
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_permissions')

    def __str__(self):
        return f"{self.user.username} - {self.project.project_name} ({self.role.name})"

    class Meta:
        db_table = 'core_permission'
        unique_together = ['user', 'project']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
            models.Index(fields=['role']),
        ]


class CostLog(models.Model):
    """
    Tracks storage costs per project over time.
    Maps to core_costlog table.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cost_logs')
    total_size_bytes = models.BigIntegerField(validators=[MinValueValidator(0)])
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.recorded_at.date()}"

    class Meta:
        db_table = 'core_costlog'
        indexes = [
            models.Index(fields=['project']),
        ]


class AuditLog(models.Model):
    """
    Tracks all permission changes and important actions (audit trail).
    Maps to core_auditlog table.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.resource_type} ({self.created_at.date()})"

    class Meta:
        db_table = 'core_auditlog'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]


class Recommendation(models.Model):
    """
    Stores AI-generated recommendations (Phase 4, optional).
    Maps to core_recommendation table.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=50)
    description = models.TextField()
    potential_savings = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recommendation_type} - {self.project.project_name}"

    class Meta:
        db_table = 'core_recommendation'
        indexes = [
            models.Index(fields=['project']),
        ]

# Create your models here.
