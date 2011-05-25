from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from bop.models import ObjectPermission


def iterify(obj):
    if hasattr(obj, '__iter__'):
        # To future self: string has __iter__ in python3
        if not isinstance(obj, basestring):
            return obj
    return [obj]
        

def grant(users, groups, permissions, objects):
    users = iterify(users)
    groups = iterify(groups)
    permissions = iterify(permissions)
    objects = iterify(objects)


def revoke(users, groups, permissions, objects):
    users = iterify(users)
    groups = iterify(users)
    permissions = iterify(users)
    objects = iterify(users)

