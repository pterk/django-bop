from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

from bop.models import ObjectPermission


class AnonymousModelBackend(object):
    """ Use a 'fake' user to store permisssions for anonymous users

    Requires a ANONYMOUS_USER_ID set in settings.py (and created in
    the admin).

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
        except AttributeError:
            raise ImproperlyConfiguredException('AnonymousBackend requires an ANONYMOUS_USER_ID in settings.py')

    def authenticate(self, username, password):
        return None

    def get_all_permissions(self, user_obj, obj=None):
        if obj:
            return self.objectbackend.get_all_permissions(self.user_obj, obj)
        else:
            return self.modelbackend.get_all_permissions(self.user_obj)
        
    def get_group_permissions(self, user_obj, obj=None):
        if obj:
            return self.objectbackend.get_group_permissions(self.user_obj, obj)
        else:
            return self.modelbackend.get_group_permissions(self.user_obj)

    def has_module_perms(self, user_obj, app_label):
        # Any point in checking object level perms?
        return self.modelbackend.has_module_perms(self.user_obj, app_label)

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

    def get_all_permissions(self, user_obj, obj=None):
        # For now this'll have to do. It gets unwieldy pretty quick
        return self.get_group_permissions(user_obj, obj=obj)
        
    def get_group_permissions(self, user_obj, obj=None):
        if obj is None:
            return set()

        ct = ContentType.objects.get_for_model(obj)
        perms = ObjectPermission.objects.filter(
            content_type=ct, object_id=obj.pk,
            group__in=user_obj.groups.all())
        perms = perms.values_list(
            'content_type__app_label', 
            'permission__codename').order_by()
        return set(["%s.%s" % (ct, name) for ct, name in perms])

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
