from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q


class ObjectPermissionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        # sanity check
        if 'bop.backends.ObjectBackend' in settings.AUTHENTICATION_BACKENDS:
            raise ImproperlyConfigured(
                'You are using bop.models.ObjectPermission'
                ' but bop.backends.ObjectBackend is not in'
                ' settings.AUTHENTICATION_BACKENDS')
        super(ObjectPermissionManager, self).__init__(*args, **kwargs)

    def get_for_model(self, model):
        """ returns all ObjectPermissions for the given model """
        ct = ContentType.objects.get_for_model(model)
        return self.filter(content_type=ct)

    def get_for_user(self, user):
        """ returns all ObjectPermissions for the given user """
        if user.is_anonymous():
            return self.none()
        return self.filter(Q(group__in=user.groups.all()) |
                           Q(user=user))

    def get_for_model_and_user(self, model, user):
        """ returns all ObjectPermissions for the given model AND user """
        if user.is_anonymous():
            return self.none()
        return self.get_for_model(model).filter(
            Q(group__in=user.groups.all()) | Q(user=user))


class UserObjectManager(models.Manager):
    def get_user_objects(self, user, permissions=None, check_model_perms=False):
        """ Will only return objects this user has permissions on

        Optionally filter for specific permissions

        This manager can be added to any Model and it will work like
        the default manager with this one extra method. 

        class MyModel(models.Model):
            name = models.CharField(max_length=255)
            ...

            objects = UserObjectManager()

        If you are already using a custommanager you can use a
        different name or perhaps add UserObjectManager as an extra
        superclass to the existing custom manager.
        """
        # importing here to avoid circular imports
        from bop.api import resolve, perm2dict, has_model_perms
        from bop.models import ObjectPermission
        # A quick check first
        if check_model_perms and not permissions:
            # If there are no specific permissions and check_model_perms
            # is set *and* the user has *any* (model) perms
            # UserObjectManager will return the entire set
            if has_model_perms(user, self.model):
                return self.all()

        if permissions:
            permissions = resolve(permissions, Permission, perm2dict)

        if check_model_perms:
            for p in permissions:
                if user.has_perm("%s.%s" % \
                                     (self.model._meta.app_label, p.codename)):
                    return self.all()

        ops = ObjectPermission.objects.get_for_model_and_user(self.model, user)

        if permissions:
            ops = ops.filter(permission__in=permissions)
        return self.filter(pk__in=ops.values_list('object_id', flat=True).distinct())
