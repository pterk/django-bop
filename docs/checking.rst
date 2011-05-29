Checking
========

Once permissions have been granted to objects you want to check these
permissions in your views and templates. Bop provides several
mechanisms to do that.

* :ref:`ObjectBackend`
* :ref:`TemplateTag`
* :ref:`ObjectPermissionManager`
* :ref:`UserObjectManager`
* :ref:`has_model_perms`

.. _ObjectBackend:

ObjectBackend
-------------

Provided you installed bop per the :doc:`instructions<installation>` you can use the
standard django method of checking for permissions in your views::

  testuser.has_perm('myapp.delete_mymodel', myobject)
  testuser.get_all_permissions(myobject)
  testuser.get_group_permissions(myobject)


.. _TemplateTag:

TemplateTag
-----------

Bop borrowed code from django-authority to provide a templatetag
:py:obj:`ifhasperm`::

    {% load permissions %}

    {% ifhasperm PERMISSION_LABEL USER OBJ %}
        lalala
    {% else %}
        meh
    {% endifhasperm %}

    {% ifhasperm "change_poll" request.user poll %}
        lalala
    {% else %}
        meh
    {% endifhasperm %}


.. _ObjectPermissionManager:

ObjectPermissionManager
-----------------------

The objectpermissionmanager has three methods to query the
ObjectPermissions granted to users:

* :py:obj:`get_for_model(model)`

  returns all ObjectPermissions for the given model

* :py:obj:`get_for_user(user)`
  
  returns all ObjectPermissions for the given user

* :py:obj:`get_for_model_and_user(model, user)`

  returns all ObjectPermissions for the given model and user


.. _UserObjectManager:

UserObjectManager
-----------------

The UserObjectManager can be added to any Model and it will work like
the default manager with one extra method:

*  :py:obj:`get_user_objects(user, permissions=None, check_model_perms=False)`

  Will only return objects the given user has permissions on and
  optionally filter for specific permissions.

You can use the manager on any model::

  from bop.managers import UserObjectManager

  class MyModel(models.Model):
      name = models.CharField(max_length=255)
      ...

      objects = UserObjectManager()

And it will work like the normal manager but rather than getting all
objects and checking the permissions in the template you can filter
the objects this user has permissions for::

  # This will return all objects for which a permission has been
  # granted to testuser
  MyModel.objects.get_for_user(testuser)

  # This will return all objects for which a *specific* permission has
  # been granted to testuser 
  MyModel.objects.get_for_user(testuser, permissions=['myapp.can_view'])

When both model- and objectpermission have been granted the manager
will, by default, only check the objectpermissions. You can override
that by setting the check_model_perms to :py:obj:`True`.


.. _has_model_perms:

has_model_perms
---------------

It is possible that some permission was granted to one model in a
module but not to another model in the same application. When
:py:obj:`get_for_user` is called with :py:obj:`check_model_perms=True`
bop checks the permissions for the *model*, not the *module* by
calling :py:obj:`bop.api.has_model_perms(user, model)`.
