from django.conf import settings
from django.contrib.auth.models import User, Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.test import TestCase

from bop.models import ObjectPermission

from bop.tests.tablemanager import TableManager
from bop.tests.models import Thing


# Dr. Szell inquires: Is it safe?
settings.ANONYMOUS_USER_ID = 2


class BasicTestCase(TestCase):
    fixtures = ['users.json', ]

    def setUp(self):
        self.anonuser  = User.objects.get(username='anon')
        self.testuser  = User.objects.get(username='test')
        self.anons     = Group.objects.get(name='anons')
        self.someperms = Group.objects.get(name='someperms')
        self.superuser = User.objects.filter(is_superuser=True)[0]
        self.anonymous = AnonymousUser()
        self.tablemanager = TableManager()
        self.tablemanager.create_table(Thing)

    def tearDown(self):
        ObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(Thing)).delete()
        self.tablemanager.drop_table(Thing)

    def test_perms(self):

        t = Thing(label='a thing')
        t.save()

        self.assertFalse(self.testuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))

        ct = ContentType.objects.get_for_model(t)
        perm = Permission.objects.get(codename='add_thing')
        ObjectPermission.objects.create(group=self.someperms,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=perm)

        self.assertFalse(self.testuser.has_perm('bop.change_thing', t))
        self.assertFalse(self.testuser.has_perm('bop.delete_thing', t))
        self.assertTrue(self.testuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.change_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.change_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.change_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonymous.has_module_perms('bop'))
        # Note: ObjectBackend.has_module_perms will never be called
        # (when AUTHENTICATION_BACKENDS is configured as intended with
        # ModelBackend (first) and ObjectBackend working in
        # conjunction. In the following case it is *ModelBackend* that
        # gets called. 
        #
        # The takeaway is: A user can have ObjectLevelPermissions for
        # a certain object but still have has_module_perms return
        # False... Such a thing should preferably be avoided...
        self.assertFalse(self.testuser.has_module_perms('bop'))
        self.assertTrue(self.superuser.has_module_perms('bop'))

    def test_manager(self):

        t = Thing(label='a thing')
        t.save()
        ct = ContentType.objects.get_for_model(t)
        perm = Permission.objects.get(codename='add_thing')

        ObjectPermission.objects.create(group=self.someperms,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=perm)

        self.assertEqual(ObjectPermission.objects.get_for_model(Thing).count(), 1)
        self.assertEqual(ObjectPermission.objects.get_for_model(t).count(), 1)
        self.assertEqual(ObjectPermission.objects.get_for_user(self.anonymous).count(), 0)
        self.assertEqual(
            ObjectPermission.objects.get_for_user(self.superuser).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.anonymous).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.superuser).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.testuser).count(), 1)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                t, self.testuser).count(), 1)
