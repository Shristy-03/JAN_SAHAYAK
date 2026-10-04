from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(*roles):
    """Require an authenticated user with one of the supplied application roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('You do not have permission to access this page.')

        return wrapped_view

    return decorator


citizen_required = role_required(User.Role.CITIZEN)
department_officer_required = role_required(User.Role.OFFICER)
administrator_required = role_required(User.Role.ADMIN)
