from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form extending Django's built-in authentication form.
    Adds styling for our frontend.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password')

class ProjectCreationForm(forms.Form):
    """
    Form for creating a new project.
    Validates that project name is unique for the user.
    """
    project_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Project Name',
            'autofocus': True
        })
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Project Description (optional)',
            'rows': 4
        })
    )

    def __init__(self, user, *args, **kwargs):
        """Store user to validate uniqueness of project name."""
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_project_name(self):
        """Ensure project name is unique for this user."""
        from .models import Project
        project_name = self.cleaned_data.get('project_name')
        
        # Check if user already has a project with this name
        if Project.objects.filter(owner=self.user, project_name=project_name).exists():
            raise forms.ValidationError(f"You already have a project named '{project_name}'.")
        
        return project_name