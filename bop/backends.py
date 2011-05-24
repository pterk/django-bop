from django.conf import settings
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

    def __init__(self, *args, **kwargs):
        self.modelbackend  = ModelBackend(*args, **kwargs)
        # TODO? Refactor so this is optional (and AnonymousBackend can
        # be used without object level permissions)
        self.objectbackend = ObjectBackend(*args, **kwargs)
        try:
            self.user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)
        except (AttributeError, User.DoesNotExist):
            #from django.core.exceptions import ImproperlyConfigured
            #raise ImproperlyConfigured('AnonymousBackend requires an ANONYMOUS_USER_ID in settings.py')
            self.user_obj = None

    def authenticate(self, username, password):
        return None

    def get_all_permissions(self, user_obj, obj=None):
        if not self.user_obj:
            return set()
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if obj:
            return self.objectbackend.get_all_permissions(self.user_obj, obj)
        else:
            return self.modelbackend.get_all_permissions(self.user_obj)
        
    def get_group_permissions(self, user_obj, obj=None):
        if not self.user_obj:
            return set()
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        if obj:
            return self.objectbackend.get_group_permissions(self.user_obj, obj)
        else:
            return self.modelbackend.get_group_permissions(self.user_obj)

    def has_module_perms(self, user_obj, app_label):
        if not self.user_obj:
            return False
        if user_obj.is_anonymous():
            user_obj = self.user_obj
        return (self.modelbackend.has_module_perms(self.user_obj, app_label) \
                    or self.objectbackend.has_module_perms(self.user_obj, app_label))

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)

    
class ObjectBackend(object):
    """ Object level permissions 

    Falls back on ModelBackend when no obj is passed

    """
    supports_object_permissions = True
    supports_anonymous_user = False

    def authenticate(self, username, password):
        return None

    def _get_obj_perms(self, user_obj, obj):
        # Not supported...
        if not isinstance(obj, models.Model):
            return ObjectPermission.objects.none()
        if user_obj.is_anonymous():
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
        return self._listify(self._get_obj_perms(user_obj, obj).filter(
                Q(group__in=user_obj.groups.all())|
                Q(user=user_obj)))

    def get_group_permissions(self, user_obj, obj=None):
        if obj is None:
            return set()
        return self._listify(self._get_obj_perms(user_obj, obj).filter(
                group__in=user_obj.groups.all()))

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)

    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.
        """
        for perm in self.get_all_permissions(user_obj):
            if perm[:perm.index('.')] == app_label:
                return True
        return False
