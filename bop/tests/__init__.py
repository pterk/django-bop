from django.conf import settings
from django.contrib.auth.models import User, Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.test import TestCase

from bop.models import ObjectPermission
from bop.api import grant, revoke

from bop.tests.tablemanager import TableManager
from bop.tests.models import Thing


class BOPTestCase(TestCase):
    fixtures = ['users.json', ]

    def get_users_and_groups(self):
        self.anonuser  = User.objects.get(username='bob_anon')
        self.testuser  = User.objects.get(username='bob_test')
        self.anons     = Group.objects.get(name='bob_anons')
        self.someperms = Group.objects.get(name='bob_someperms')
        self.superuser = User.objects.filter(is_superuser=True)[0]
        self.anonymous = AnonymousUser()

    def setUp(self):
        self._anonymous_user_id = getattr(settings, 'ANONYMOUS_USER_ID', None)
        self._backends = getattr(settings, 'AUTHENTICATION_BACKENDS', None)
        self.get_users_and_groups()
        self.tablemanager = TableManager()
        self.tablemanager.create_table(Thing)
        self.thing = Thing(label='a thing')
        self.thing.save()

        if self._anonymous_user_id:
            delattr(settings, 'ANONYMOUS_USER_ID')

    def tearDown(self):
        if self._anonymous_user_id:
            settings.ANONYMOUS_USER_ID = self._anonymous_user_id
        settings.AUTHENTICATION_BACKENDS = self._backends
        ObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(Thing)).delete()
        self.tablemanager.drop_table(Thing)


class TestAnonymousModelBackendNoAnon(BOPTestCase):
    def setUp(self):
        super(TestAnonymousModelBackendNoAnon, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['bop.backends.AnonymousModelBackend']

    def tearDown(self):
        super(BOPTestCase, self).tearDown()
        self.someperms.permissions.clear()
        self.testuser.user_permissions.clear()
        self.anonuser.user_permissions.clear()

    def test(self):
        t = self.thing
        self.assertFalse(self.testuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.add_thing', t))

        # Add a permission to a group
        ct = ContentType.objects.get_for_model(t)

        perma = Permission.objects.get(codename='add_thing', content_type=ct)
        self.someperms.permissions.add(perma)

        permd = Permission.objects.get(codename='delete_thing', content_type=ct)

        self.testuser.user_permissions.add(permd)
        self.anonuser.user_permissions.add(permd)

        # reloading to clear the (permissions) cache
        self.get_users_and_groups()

        self.assertFalse(self.testuser.has_perm('bop.change_thing', t))
        self.assertTrue(self.testuser.has_perm('bop.delete_thing'))
        self.assertTrue(self.testuser.has_perm('bop.delete_thing', t))
        self.assertTrue(self.testuser.has_perm('bop.add_thing'))
        self.assertTrue(self.testuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.change_thing', t))
        self.assertTrue(self.anonuser.has_perm('bop.delete_thing'))
        self.assertTrue(self.anonuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.change_thing', t))
        if hasattr(settings, 'ANONYMOUS_USER_ID'):
            self.assertTrue(self.anonymous.has_perm('bop.delete_thing'))
            self.assertTrue(self.anonymous.has_perm('bop.delete_thing', t))
            self.assertTrue(self.anonymous.has_module_perms('bop'))
        else:
            self.assertFalse(self.anonymous.has_perm('bop.delete_thing'))
            self.assertFalse(self.anonymous.has_perm('bop.delete_thing', t))
            self.assertFalse(self.anonymous.has_module_perms('bop'))
        self.assertTrue(self.anonuser.has_module_perms('bop'))

        self.assertTrue(self.testuser.has_module_perms('bop'))
        self.assertTrue(self.superuser.has_module_perms('bop'))


class TestAnonymousModelBackendNoAnonPlus(TestAnonymousModelBackendNoAnon):
    def setUp(self):
        super(TestAnonymousModelBackendNoAnonPlus, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'bop.backends.AnonymousModelBackend']


class TestAnonymousModelBackendWithAnon(TestAnonymousModelBackendNoAnon):
    def setUp(self):
        super(TestAnonymousModelBackendWithAnon, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['bop.backends.AnonymousModelBackend']
        settings.ANONYMOUS_USER_ID = 2


class TestAnonymousModelBackendWithAnonPlus(TestAnonymousModelBackendNoAnon):
    def setUp(self):
        super(TestAnonymousModelBackendWithAnonPlus, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'bop.backends.AnonymousModelBackend']
        settings.ANONYMOUS_USER_ID = 2


class TestObjectBackendNoAnonymous(BOPTestCase):
    def setUp(self):
        super(TestObjectBackendNoAnonymous, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['bop.backends.ObjectBackend']

    def test_perms(self):

        t = self.thing
        self.assertFalse(self.testuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))

        ct = ContentType.objects.get_for_model(t)

        # Add a permission to a group
        ct = ContentType.objects.get_for_model(t)
        permg = Permission.objects.get(codename='add_thing')
        ObjectPermission.objects.create(group=self.someperms,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=permg)

        # And another 'a' user
        permu = Permission.objects.get(codename='delete_thing')
        ObjectPermission.objects.create(user=self.testuser,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=permu)

        # And another 'a' user
        perma = Permission.objects.get(codename='delete_thing')
        ObjectPermission.objects.create(user=self.anonuser,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=perma)

        self.assertFalse(self.testuser.has_perm('bop.change_thing', t))
        self.assertFalse(self.testuser.has_perm('bop.delete_thing'))
        self.assertTrue(self.testuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.testuser.has_perm('bop.add_thing'))
        self.assertTrue(self.testuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.add_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.change_thing', t))
        self.assertTrue(self.superuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.change_thing', t))
        self.assertFalse(self.anonuser.has_perm('bop.delete_thing'))
        self.assertTrue(self.anonuser.has_perm('bop.delete_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.add_thing', t))
        self.assertFalse(self.anonymous.has_perm('bop.change_thing', t))
        if hasattr(settings, 'ANONYMOUS_USER_ID'):
            self.assertFalse(self.anonymous.has_perm('bop.delete_thing'))
            self.assertTrue(self.anonymous.has_perm('bop.delete_thing', t))
        else:
            self.assertFalse(self.anonymous.has_perm('bop.delete_thing'))
            self.assertFalse(self.anonymous.has_perm('bop.delete_thing', t))
        # Note: ObjectBackend.has_module_perms will never be called
        # (when AUTHENTICATION_BACKENDS is configured as intended with
        # ModelBackend (first) and ObjectBackend working in
        # conjunction. In the following case it is *ModelBackend* that
        # gets called. 
        #
        # The takeaway is: A user can have ObjectLevelPermissions for
        # a certain object but still have has_module_perms return
        # False... Such a thing should preferably be avoided...
        self.assertFalse(self.anonuser.has_module_perms('bop'))
        self.assertFalse(self.anonymous.has_module_perms('bop'))
        self.assertFalse(self.testuser.has_module_perms('bop'))
        self.assertTrue(self.superuser.has_module_perms('bop'))

    def test_manager(self):

        t = self.thing

        self.assertEqual(ObjectPermission.objects.get_for_model(Thing).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model(t).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_user(self.anonymous).count(), 0)
        self.assertEqual(
            ObjectPermission.objects.get_for_user(self.testuser).count(), 0)
        self.assertEqual(
            ObjectPermission.objects.get_for_user(self.superuser).count(), 0)

        ct = ContentType.objects.get_for_model(t)

        perm = Permission.objects.get(codename='add_thing')
        ObjectPermission.objects.create(group=self.someperms,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=perm)

        permd = Permission.objects.get(codename='delete_thing')
        ObjectPermission.objects.create(user=self.testuser,
                                        content_type=ct,
                                        object_id=t.id,
                                        permission=permd)

        self.assertEqual(ObjectPermission.objects.get_for_model(Thing).count(), 2)
        self.assertEqual(ObjectPermission.objects.get_for_model(t).count(), 2)
        self.assertEqual(ObjectPermission.objects.get_for_user(self.anonymous).count(), 0)
        self.assertEqual(
            ObjectPermission.objects.get_for_user(self.testuser).count(), 2)
        self.assertEqual(
            ObjectPermission.objects.get_for_user(self.superuser).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.anonymous).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.superuser).count(), 0)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                Thing, self.testuser).count(), 2)
        self.assertEqual(ObjectPermission.objects.get_for_model_and_user(
                t, self.testuser).count(), 2)


class TestObjectBackendNoAnonymousPlus(TestObjectBackendNoAnonymous):
    def setUp(self):
        super(TestObjectBackendNoAnonymous, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'bop.backends.ObjectBackend']


class TestObjectBackendWithAnonymous(TestObjectBackendNoAnonymous):
    def setUp(self):
        super(TestObjectBackendWithAnonymous, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['bop.backends.ObjectBackend']
        settings.ANONYMOUS_USER_ID = 2


class TestObjectBackendWithAnonymousPlus(TestObjectBackendNoAnonymous):
    def setUp(self):
        super(TestObjectBackendWithAnonymousPlus, self).setUp()
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'bop.backends.ObjectBackend']
        settings.ANONYMOUS_USER_ID = 2


class TestAPI(TestCase):
    def setUp(self):
        self._anonymous_user_id = getattr(settings, 'ANONYMOUS_USER_ID', None)
        self._backends = getattr(settings, 'AUTHENTICATION_BACKENDS', None)
        self.tablemanager = TableManager()
        self.tablemanager.create_table(Thing)
        self.thing = Thing(label='a thing')
        self.thing.save()
        if self._anonymous_user_id:
            delattr(settings, 'ANONYMOUS_USER_ID')

    def tearDown(self):
        if self._anonymous_user_id:
            settings.ANONYMOUS_USER_ID = self._anonymous_user_id
        settings.AUTHENTICATION_BACKENDS = self._backends
        ObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(Thing)).delete()
        self.tablemanager.drop_table(Thing)

    def testGrant(self):
        testa = User.objects.create_user('test-a', 'test@example.com.invalid', 'test-a')
        testb = User.objects.create_user('test-b', 'test@example.com.invalid', 'test-b')
        testga, _ = Group.objects.get_or_create(name='test-ga')
        testgb, _ = Group.objects.get_or_create(name='test-gb')
        testa.groups.add(testga)
        testb.groups.add(testgb)
        perms = Permission.objects.all()
        objects = self.thing
        grant([testa], [testga, testgb], perms, objects)
