import operator

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from bop.models import ObjectPermission


def get_model_perms(model):
    return [p[0] for p in model._meta.permissions] + \
        [model._meta.get_add_permission(), 
         model._meta.get_change_permission(), 
         model._meta.get_delete_permission()]


def has_model_perms(user, model):
    for perm in user.get_all_permissions():
        app_label, codename = perm.split('.')
        if model._meta.app_label == app_label and \
                codename in get_model_perms(model):
            return True
    return False


# I terify: BOO!
def iterify(obj, exceptions=(basestring,)):
    """ iteryfy makes sure `obj` is iterable 
    
    (by turning any value that isn't iterable into a list)

    >>> from bop.api import iterify 
    >>> things = [1, "string", ('a', 'tuple'), {'name': 'dict', 'another': 'value'}, set(['test', 1, 3]), [1,3,4], None, [None]]
    >>> for thing in things:
    ...     for x in iterify(thing):
    ...         print x
    ... 
    1
    string
    a
    tuple
    name
    another
    test
    1
    3
    1
    3
    4
    None
    None
    >>>
    >>> for thing in things:
    ...     for x in iterify(thing, (basestring, dict)):
    ...         if isinstance(x, dict):
    ...             d = x.items()
    ...             d.sort()
    ...             print d
    ...         else:
    ...             print x
    ... 
    1
    string
    a
    tuple
    [('another', 'value'), ('name', 'dict')]
    test
    1
    3
    1
    3
    4
    None
    None
    >>>
    """
    if hasattr(obj, '__iter__'):
        # To future self: string has __iter__ in python3
        if not isinstance(obj, exceptions):
            return obj
    return [obj]
        

def resolve(iterable, model, key=None):
    resolved = []
    for i in iterify(iterable):
        if isinstance(i, model):
            resolved.append(i)
        if isinstance(i, (basestring, int)):
            if key is None or isinstance(key ,int):
                key = 'pk'
            if hasattr(key, '__call__'):
                i = key(i)
            else:
                i = {key: i}
        if isinstance(i, dict):
            try:
                resolved.append(model.objects.get(**i))
            except model.DoesNotExist:
                pass
    return resolved


def is_object_permission(obj, permission, ct):
    return permission.content_type == ct and \
        obj._meta.app_label == permission.content_type.app_label and \
        permission.codename in get_model_perms(obj)
        #(permission.codename in [x[0] for x in obj._meta.permissions] \
        #     or permission.codename in (obj._meta.get_add_permission(), 
        #                                obj._meta.get_change_permission(), 
        #                                obj._meta.get_delete_permission()))


def perm2dict(perm):
    app_label, codename = perm.split(".")
    return {"content_type__app_label": app_label, "codename": codename}


def _make_lists_of_objects(users, groups, permissions, objects):
    # Make sure all 'objects' are model-instances
    users = resolve(users, User, key='username')
    groups = resolve(groups, Group, key='name')
    permissions = resolve(permissions, Permission, key=perm2dict)
    # objects *must* be model-instances already
    return (users, groups, permissions, iterify(objects))


def grant(users, groups, permissions, objects):
    users, groups, permissions, objects = \
        _make_lists_of_objects(users, groups, permissions, objects)
    for o in objects:
        if not hasattr(o, '_meta'):
            continue
        ct = ContentType.objects.get_for_model(o)
        for p in permissions:
            if is_object_permission(o, p, ct):
                for u in users:
                    ObjectPermission.objects.get_or_create(user=u,
                                                           permission=p,
                                                           object_id=o.id,
                                                           content_type=ct)
                for g in groups:
                    ObjectPermission.objects.get_or_create(group=g,
                                                           permission=p,
                                                           object_id=o.id,
                                                           content_type=ct)
    

def revoke(users, groups, permissions, objects):
    users, groups, permissions, objects = \
        _make_lists_of_objects(users, groups, permissions, objects)
    userlist = []
    grouplist = []
    for o in objects:
        ct = ContentType.objects.get_for_model(o)
        for p in permissions:
            if is_object_permission(o, p, ct):
                for u in users:
                    userlist.append(Q(user=u))
                for g in groups:
                    grouplist.append(Q(group=g))
                Qs = userlist+grouplist
                if not Qs:
                    continue
                ObjectPermission.objects.filter(
                    reduce(operator.or_, Qs),
                    content_type=ct, object_id=o.id,permission=p
                    ).delete()

