from rest_framework import permissions
from apps.connections.models import Connection
class IsAdmin(permissions.BasePermission):
    """Check if user is admin based on role field"""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) == 'admin'
        )

class IsEmployer(permissions.BasePermission):
    """Check if user is employer based on role field"""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) == 'employer'
        )

class IsJobSeeker(permissions.BasePermission):
    """Check if user is jobseeker based on role field"""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) == 'jobseeker'
        )

class IsStaff(permissions.BasePermission):
    """Check if user is staff (Django admin)"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class IsSuperUser(permissions.BasePermission):
    """Check if user is superuser"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check various possible owner relationships
        owner_attrs = ['user', 'author', 'jobseeker', 'employer', 'recruiter', 'applicant']
        for attr in owner_attrs:
            if hasattr(obj, attr):
                return getattr(obj, attr) == request.user
        
        return obj == request.user

class IsConnectionParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in [obj.connection.from_user, obj.connection.to_user]

class CanChatWithUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user_id = view.kwargs.get('user_id')
        if not user_id:
            return False
        
        # Check if there's an accepted connection between current user and target user
        return (
            Connection.objects.filter(
                status='accepted',
                from_user=request.user,
                to_user_id=user_id
            ).exists() or 
            Connection.objects.filter(
                status='accepted',
                from_user_id=user_id,
                to_user=request.user
            ).exists()
        )