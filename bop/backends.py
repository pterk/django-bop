from django.conf import settings
from django.contrib.auth import get_backends
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from bop.models import ObjectPermission


class AnonymousModelBackend(object):
    """ Use a 'fake' user to store permisssions for anonymous users

    Requires a ANONYMOUS_USER_ID set in settings.py (and created in
    the database).
    """
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def __init__(self, *args, **kwargs):
        self.modelbackend  = ModelBackend(*args, **kwargs)
        self.user_obj = None
        try:
            self.user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)
        except (AttributeError, User.DoesNotExist):
            pass
            # Commented out because of ugly warnings in django's tests 
            #
            # import warnings
            # warnings.warn(
            #     "bop.backends.AnonymousModelBackend is enabled in "
            #     "settings.AUTHENTICATION_BACKENDS. This requires "
            #     "settings.ANONYMOUS_USER_ID to be set and a user with "
            #     "that id to be created in the database.")

    def authenticate(self, username, password):
        return None

    def get_all_permissions(self, user_obj, obj=None):
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if user_obj and user_obj.is_active:
            return self.modelbackend.get_all_permissions(user_obj)
        return set()

    def get_group_permissions(self, user_obj, obj=None):
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if user_obj and user_obj.is_active:
            return self.modelbackend.get_group_permissions(user_obj)
        return set()

    def has_module_perms(self, user_obj, app_label):
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if user_obj and user_obj.is_active:
            return self.modelbackend.has_module_perms(user_obj, app_label)
        return False

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj)

    
class ObjectBackend(object):
    """ Object level perms (for models known in contrib.contenttypes!)

    With (optional) support for anonymous users. 

    Inactive users are supported to the extend that their
    permission-set is always empty.

    CAVEAT: This only works with objects from models that are known in
    django.contrib.contenttypes.models.ContentType. For other types of
    objects this backend will return an empty set.
    """
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def __init__(self, *args, **kwargs):
        self.user_obj = None
        try:
            self.user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)
        except (AttributeError, User.DoesNotExist):
            pass

    def authenticate(self, username, password):
        return None

    def _get_obj_perms(self, user_obj, obj):
        # Not supported...
        if not isinstance(obj, models.Model):
            return ObjectPermission.objects.none()
        ct = ContentType.objects.get_for_model(obj)
        return ObjectPermission.objects.filter(
            content_type=ct, object_id=obj.pk)

    def _listify(self, perms):
        perms = perms.values_list(
            'content_type__app_label', 
            'permission__codename')
        return set(["%s.%s" % (ct, name) for ct, name in perms])

    def get_all_permissions(self, user_obj, obj=None):
        if obj is None:
            return set()
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if user_obj and user_obj.is_active:
            return self._listify(self._get_obj_perms(user_obj, obj).filter(
                    Q(group__in=user_obj.groups.all())|
                    Q(user=user_obj)))
        return set()

    def get_group_permissions(self, user_obj, obj=None):
        if obj is None:
            return set()
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if user_obj and user_obj.is_active:
            return self._listify(self._get_obj_perms(user_obj, obj).filter(
                    group__in=user_obj.groups.all()))
        return set()

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)

    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.

        Note: If this backend is used, as recommended, in conjunction
        with ModelBackend then this method wil never be called.
        """
        for perm in self.get_all_permissions(user_obj):
            if perm[:perm.index('.')] == app_label:
                return True
        return False
