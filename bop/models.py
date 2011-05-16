from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class ObjectPermissionManager(models.Manager):

    def get_for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        return self.filter(content_type=ct)

    def get_for_user(self, user):
        if user.is_anonymous():
            user=User.objects.get(id=settings.ANONYMOUS_USER_ID)
        return self.filter(group__in=user.groups.all())

    def get_for_model_and_user(self, model, user):
        ct = ContentType.objects.get_for_model(model)
        if user.is_anonymous():
            user=User.objects.get(id=settings.ANONYMOUS_USER_ID)
        return self.filter(group__in=user.groups.all(),
                           content_type=ct)
        

class ObjectPermission(models.Model):
    group = models.ForeignKey(Group)
    permission   = models.ForeignKey(Permission)
    content_type = models.ForeignKey(ContentType)
    object_id    = models.PositiveIntegerField()
    object       = generic.GenericForeignKey('content_type', 'object_id')

    objects      = ObjectPermissionManager()

    class Meta:
        unique_together = ('content_type', 'object_id', 'permission', 'group')

    def __unicode__(self):
        return "Group '%s' has '%s' permission on %s" % \
            (self.group, self.permission.codename, repr(self.object))
