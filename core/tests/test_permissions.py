from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Project, Role, Permission


class PermissionDecoratorTests(TestCase):
    """
    Tests for permission decorators.
    Verifies that @requires_project_permission and @requires_role work correctly.
    """

    def setUp(self):
        """Set up test data: users, roles, projects, permissions."""
        self.client = Client()
        
        # Create users
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.editor = User.objects.create_user(username='editor', password='testpass123')
        self.viewer = User.objects.create_user(username='viewer', password='testpass123')
        self.unauthorized = User.objects.create_user(username='unauthorized', password='testpass123')
        
        # Create roles
        self.admin_role = Role.objects.create(name='Admin', description='Full access')
        self.editor_role = Role.objects.create(name='Editor', description='Can edit')
        self.viewer_role = Role.objects.create(name='Viewer', description='Read-only')
        
        # Create project owned by owner
        self.project = Project.objects.create(
            project_name='Test Project',
            description='A test project',
            owner=self.owner
        )
        
        # Grant permissions to editor and viewer
        Permission.objects.create(
            user=self.editor,
            project=self.project,
            role=self.editor_role,
            granted_by=self.owner
        )
        Permission.objects.create(
            user=self.viewer,
            project=self.project,
            role=self.viewer_role,
            granted_by=self.owner
        )

    def test_owner_can_access_project(self):
        """Test that project owner can access their project."""
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(f'/project/{self.project.id}/')
        self.assertEqual(response.status_code, 200)

    def test_user_with_permission_can_access_project(self):
        """Test that user with explicit permission can access project."""
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(f'/project/{self.project.id}/')
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_cannot_access_project(self):
        """Test that user without permission is redirected."""
        self.client.login(username='unauthorized', password='testpass123')
        response = self.client.get(f'/project/{self.project.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        self.assertRedirects(response, '/dashboard/')