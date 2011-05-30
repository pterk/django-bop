Checking
========

Once permissions have been granted to objects you want to check these
permissions in your views and templates. Bop provides several
mechanisms to do that.

* :ref:`ObjectBackend`
* :ref:`Decorator`
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


.. _Decorator:

Decorator
---------

The :py:obj:`user_has_object_level_perm` decorator checks wether a
user has permission to access an object::

  :py:obj:`user_has_object_level_perm`(perm, model, pkfield='pk', login_url=None, redirect_field_name=REDIRECT_FIELD_NAME)

The :py:obj:`pkfield` is expected to be passed to the view as a
keyword argument.

The object will be obtained by doing::

    Model.objects.get(**{pkfield:kwargs[pkfield]})

An example will perhaps better illustrate::

   # In urls.py
   ...
   (r'^articles/(\d{4})/(\d{2})/(?P<article_id>\d+)/$', 'news.views.article_detail'),
   ...


   # In views.py
   from bop.decorators import user_has_object_level_perm

   from news.models import Article


   @user_has_object_level_perm('news.view_article', Article, pkfield='article_id')
   def view article_detail(year, month, article_id):
       pass

Note that the :py:obj:`pkfield` must be using `named groups` so the
decorator can actually find the keyword argument in \*\*kwargs.

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
