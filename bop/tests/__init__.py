from django.conf import settings
from django.contrib.auth.models import User, Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import QuerySet
from django.test import TestCase

from bop.models import ObjectPermission
from bop.api import grant, revoke

from bop.tests.tablemanager import TableManager
from bop.tests.models import Thing


class BOPTestCase(TestCase):
    fixtures = ['users.json', ]

    def get_users_and_groups(self):
        self.anonuser  = User.objects.get(username='bop_anon')
        self.testuser  = User.objects.get(username='bop_test')
        self.anons     = Group.objects.get(name='bop_anons')
        self.someperms = Group.objects.get(name='bop_someperms')
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
        self.content_type = ContentType.objects.get_for_model(Thing)
        if self._anonymous_user_id:
            delattr(settings, 'ANONYMOUS_USER_ID')

    def tearDown(self):
        if self._anonymous_user_id:
            settings.ANONYMOUS_USER_ID = self._anonymous_user_id
        settings.AUTHENTICATION_BACKENDS = self._backends
        ObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(Thing)).delete()
        self.tablemanager.drop_table(Thing)

    def testHasModelPerms(self):
        from bop.api import has_model_perms, get_model_perms
        self.assertEqual(get_model_perms(Thing) ,get_model_perms(self.thing))
        testa = User.objects.create_user('test-a', 'test@example.com.invalid', 'test-a')
        self.assertFalse(has_model_perms(testa, Thing))
        ct = ContentType.objects.get_for_model(Thing)
        permd = Permission.objects.get(codename='delete_thing', content_type=ct)
        testa.user_permissions.add(permd)
        # re-get the user to clear/re-fill the perms-cache
        testa = User.objects.get(username='test-a')
        self.assertTrue(has_model_perms(testa, Thing))
        testa.delete()
        

    def testGrantRevoke(self):
        testa = User.objects.create_user('test-a', 'test@example.com.invalid', 'test-a')
        testb = User.objects.create_user('test-b', 'test@example.com.invalid', 'test-b')
        testga, _ = Group.objects.get_or_create(name='test-ga')
        testgb, _ = Group.objects.get_or_create(name='test-gb')
        testa.groups.add(testga)
        testb.groups.add(testgb)
        perms = Permission.objects.filter(content_type=self.content_type)
        objects = self.thing
        self.assertEqual(ObjectPermission.objects.count(), 0)
        grant([testa], [testga, testgb], perms, objects)
        self.assertEqual(ObjectPermission.objects.count(), 15)
        revoke(None, [testga, testgb], perms, objects)
        revoke(None, [testga, testgb], perms, objects)
        self.assertEqual(ObjectPermission.objects.count(), 5)
        # Try again (should have no consequences)
        revoke(None, [testga, testgb], perms, objects)
        self.assertEqual(ObjectPermission.objects.count(), 5)
        # arbitrary object
        grant([testa], [testga, testgb], perms, object())
        self.assertEqual(ObjectPermission.objects.count(), 5)
        # Just pass names (except for  the objects)
        grant(None, testga.name, 'bop.delete_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        # non-existing permisions
        grant(None, testga.name, 'bop.wrong_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        revoke(None, testga.name, 'bop.wrong_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        # non-existing group
        grant(None, 'InternationalOrganisationOfAnarchists', 'bop.change_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        revoke(None, 'InternationalOrganisationOfAnarchists', 'bop.change_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        # non-existing user
        grant(AnonymousUser(), None, 'bop.change_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        revoke(AnonymousUser(), None, 'bop.change_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 6)
        revoke(None, testga.name, 'bop.delete_thing', self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 5)
        # use a queryset: revoke thing-perms (see above) for all users
        revoke(User.objects.all(), None, perms, self.thing)
        self.assertEqual(ObjectPermission.objects.count(), 0)
        testa.delete()
        testb.delete()
        testga.delete()
        testgb.delete()


class TestUserObjectManager(BOPTestCase):

    def test(self):
        from bop.managers import UserObjectManager
        UserObjectManager().contribute_to_class(Thing, 'objects')
        self.assertEqual(Thing.objects.count(), 1)
        self.assertEqual(ObjectPermission.objects.get_for_model(Thing).count(), 0)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser).count(), 0)
        thinga = Thing(label='thinga')
        thinga.save()
        thingb = Thing(label='thingb')
        thingb.save()
        grant(self.testuser, None, 'bop.change_thing', thinga)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser).count(), 1)
        grant(self.testuser, None, 'bop.do_thing', thinga)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser).count(), 1)
        grant(self.testuser, None, 'bop.do_thing', thingb)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser).count(), 2)
        # Now check for a specific perm
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, 'bop.do_thing').count(), 2)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, permissions='bop.change_thing').count(), 1)
        # And now for something completely different
        ct = ContentType.objects.get_for_model(Thing)
        permd = Permission.objects.get(codename='delete_thing', content_type=ct)
        self.testuser.user_permissions.add(permd)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, 'bop.change_thing').count(), 1)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, permissions='bop.change_thing').count(), 1)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, 'bop.delete_thing', True).count(), 3)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, check_model_perms=True).count(), 3)
        self.assertEqual(Thing.objects.get_user_objects(self.testuser, None, True).count(), 3)


class TestNoObjectBackend(BOPTestCase):
    def __init__(self, *args, **kwargs):
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
        super(TestNoObjectBackend, self).__init__(*args, **kwargs)
        
    def test(self):
        self.assertRaises(ImproperlyConfigured, _ = ObjectPermission.objects.all())
