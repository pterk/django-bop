from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class ObjectPermissionManager(models.Manager):

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
        ct = ContentType.objects.get_for_model(model)
        return self.filter((Q(group__in=user.groups.all()) |
                            Q(user=user)),
                           content_type=ct)
        

class ObjectPermission(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    permission = models.ForeignKey(Permission)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

    objects      = ObjectPermissionManager()

    class Meta:
        unique_together = ('content_type', 'object_id', 'permission', 'group', 'user')

    def clean(self):
        if (self.user is None and self.group is None) or \
                (self.user and self.group):
            raise ValidationError('You *must* provide EITHER a user OR a group. (Not neither nor both.)')

    def __unicode__(self):
        if self.user:
            return "User '%s' has '%s' permission on %s" % \
                (self.user, self.permission.codename, repr(self.object))
        else:
            return "Group '%s' has '%s' permission on %s" % \
                (self.group, self.permission.codename, repr(self.object))
