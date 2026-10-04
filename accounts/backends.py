from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate an active user by their email address or username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get('email')
        if not identifier or not password:
            return None

        user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            user = User.objects.filter(username__iexact=identifier).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
