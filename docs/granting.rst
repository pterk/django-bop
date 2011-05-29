Usage
=====

Once installed you will want to start granting permissions to your
objects. django-bop provides three tools to help you with that:

* :ref:`ObjectAdmin`
* :ref:`form-factory`
* :ref:`API`

.. _ObjectAdmin:

ObjectAdmin
------------

By subclassing ObjectAdmin in admin.py (in stead of ModelAdmin) you
can manage the objects in the django admin. Each object (detail page)
will have inline forms to grant / revoke (delete) permissions.

The admin will also filter out objects that the user doesn't have
acces to or deny actions he/she doesn't have permissions for.

In admin.py::

  from django.contrib import admin

  from bop.admin import ObjectAdmin

  from myapp.models import MyModel


  class MyModelAdmin(ObjectAdmin):
      # All the usual options work here
      pass


  admin.site.register(MyModel, MyModelAdmin)
  admin.site.register(Log)


.. _form-factory:

Form Factory
------------

If you want to have the inlines in your own (Model)forms you can use
the inline_permissions_form_factory to generate a formset that will
handle the permissions for you::

  # TODO Example
  from bop.forms import inline_permissions_form_factory


.. _API:

API
---

Bop provides two very flexible functions to grant and revoke
permissions for objects to users and groups::

  from bop.api import grant, revoke

  grant([mymodeladmin, testuser], None, 'myapp.delete_mymodel', MyModel.objects.filter(owner=testuser))

  revoke(testuser, None, 'myapp.delete_mymodel', MyModel.objects.filter(id=1))

Both functions have the same signature: users, groups, permissions,
objects. All arguments can be a single item or an iterable.::

   grant(User.objects.all(), Group.objects.all(), 'myapp.can_view', MyModel.objects.all())

Users, groups and permissions can be either a string or an object.

* For users a string, or iterable of strings, will be converted into a
  User object by doing User.objects.get(username=user)

* For groups a string will be converted into a Group object by doing
  Group.objects.get(name=group)

* For permisions a string will be converted into a Permission object
  by doing (simplefied here)
  Permission.objects.get(app_label=app_label, codename=codename)

Objects however must be instances of a model that is 'registered' /
known in django.contrib.contenttyes.
