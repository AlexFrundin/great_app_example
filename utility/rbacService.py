""" 
 Service for role based access control.
 Provides simple method for checking permissions.
"""
from functools import wraps
from rest_framework import status
from config.messages import Messages
from rest_framework.response import Response
from users.models import RolePermission, User

# Decorator function to check user authentication
def RbacService(permission):
    """
    Check the existence of the permissions or attributes on the user of the given rbacArray
    returns True, if the user has any combination of permissions, False otherwise
    """
    def inner_function(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            try:
                # role permission
                role_permissions = []
                role_permission_info = RolePermission.objects.filter(permission = permission).values()
                for role_permission in role_permission_info:
                    role_permissions.append(role_permission['role_id'])
                # check user permission
                user_permission = User.objects.filter(id=request.user_id, role__in=role_permissions, is_active=1, is_deleted=0).values()
                if user_permission:
                    return function(request, *args, **kwargs)
                else:
                    return Response({'error': Messages.PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
            except Exception as exception:
                return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return wrap
    return inner_function


def process_exception(self, request, exception):
    print(exception.__class__.__name__)
    print(exception.message)
    return None
