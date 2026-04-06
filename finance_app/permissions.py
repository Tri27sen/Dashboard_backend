"""
Custom permission classes for role-based access control.

Implements fine-grained permissions based on user roles:
- Viewer: Read-only access to transactions and dashboard
- Analyst: Read and write access to own transactions
- Admin: Full administrative access
"""

from rest_framework import permissions
from finance_app.models import User


class IsViewer(permissions.BasePermission):
    """Permission: User has 'viewer' role or higher."""
    message = "Only viewers and above can access this."
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['viewer', 'analyst', 'admin']


class IsAnalyst(permissions.BasePermission):
    """Permission: User has 'analyst' role or higher."""
    message = "Only analysts and admins can access this."
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['analyst', 'admin']


class IsAdmin(permissions.BasePermission):
    """Permission: User has 'admin' role."""
    message = "Only admins can access this."
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name == 'admin'


class IsSupervisor(permissions.BasePermission):
    """
    Permission: User is admin or can manage their own data.
    Used for view permissions where analysts can see their own data.
    """
    message = "You don't have permission to access this resource."
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['analyst', 'admin']
    
    def has_object_permission(self, request, view, obj):
        # Admin can access any object
        if request.user.role.name == 'admin':
            return True
        # Analyst can only access their own data
        if request.user.role.name == 'analyst':
            return obj.user == request.user
        return False


class CanCreateTransaction(permissions.BasePermission):
    """Permission: User can create financial transactions."""
    message = "Only analysts and admins can create transactions."
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Viewers can read
            if hasattr(request.user, 'role'):
                return request.user.role.name in ['viewer', 'analyst', 'admin']
        
        # Only analysts and admins can create
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['analyst', 'admin']


class CanEditTransaction(permissions.BasePermission):
    """Permission: User can edit/delete transactions they own or admin can edit any."""
    message = "You can only edit your own transactions."
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            if hasattr(request.user, 'role'):
                return request.user.role.name in ['viewer', 'analyst', 'admin']
        
        # Only analysts and admins can modify
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['analyst', 'admin']
    
    def has_object_permission(self, request, view, obj):
        # Admin can modify any transaction
        if request.user.role.name == 'admin':
            return True
        
        # Analyst can only modify their own transactions
        if request.user.role.name == 'analyst':
            return obj.user == request.user
        
        return False


class CanManageUsers(permissions.BasePermission):
    """Permission: Only admins can manage users."""
    message = "Only admins can manage users."
    
    def has_permission(self, request, view):
        if request.method == 'GET':
            # Only admins can list all users
            if not request.user or not hasattr(request.user, 'role'):
                return False
            return request.user.role.name == 'admin'
        
        # Only admins can create/update/delete users
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name == 'admin'
    
    def has_object_permission(self, request, view, obj):
        # Only admins can access user objects
        if not hasattr(request.user, 'role'):
            return False
        return request.user.role.name == 'admin'


class IsActive(permissions.BasePermission):
    """Permission: User account must be active."""
    message = "Your account has been deactivated."
    
    def has_permission(self, request, view):
        if not hasattr(request.user, 'is_active'):
            return False
        return request.user.is_active


class CanAccessDashboard(permissions.BasePermission):
    """Permission: User can access dashboard (all authenticated users)."""
    message = "You don't have permission to access the dashboard."
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        # All roles can access dashboard
        return request.user.role.name in ['viewer', 'analyst', 'admin']