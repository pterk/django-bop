from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from bop.managers import ObjectPermissionManager


class ObjectPermission(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    permission = models.ForeignKey(Permission)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(index=True)
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
