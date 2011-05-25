from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q


class ObjectPermissionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        if 'bop.backends.ObjectBackend' in settings.AUTHENTICATION_BACKENDS:
            raise ImproperlyConfigured(
                'You are using bop.models.ObjectPermission'
                ' but bop.backends.ObjectBackend is not in'
                ' settings.AUTHENTICATION_BACKENDS')
        super(ObjectPermissionManager, self).__init__(*args, **kwargs)

    def get_for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        return self.filter(content_type=ct)

    def get_for_user(self, user):
        if user.is_anonymous():
            return self.none()
        return self.filter(Q(group__in=user.groups.all()) |
                           Q(user=user))

    def get_for_model_and_user(self, model, user):
        if user.is_anonymous():
            return self.none()
        return self.get_for_model(model).filter(
            Q(group__in=user.groups.all()) | Q(user=user))
