django-bop
==========

Django-bop provides Basic Object-level Permissions for django 1.2 and
later. It is based on the django-advent article_ 'Object Permissions'
by Florian Apolloner.

Although there are a few other_ permission backends I wanted a
simple(r) backend that closely matches the existing django
functionality.

Installation
------------

* Install it in your (virtual) environment:

  $ pip install django-bop

* Add 'bop' to you INSTALLED_APPS in settings.py

* While in settings.py specify the AUTHENTICATION_BACKENDS:

  AUTHENTICATION_BACKENDS = (
      'django.contrib.auth.backends.ModelBackend',
      'bop.backends.ObjectBackend',
  )

If you want to give permissions to anonymous user you should do the following:

* Add a user to contrib.auth.models.User to represent anonymous users
  (e.g. via the admin). Give it an appropriate name (anon / anonymous)
  so it easily recognized when assigning permissions.

* Add ANONYMOUS_USER_ID to settings.py::

  ANONYMOUS_USER_ID = 2

If, in addition, you want to support Model-permissions for anonymous
users:

* Add the AnonymousModelBackend::

  AUTHENTICATION_BACKENDS = (
      'django.contrib.auth.backends.ModelBackend',
      'bop.backends.AnonymousModelBackend',
      'bop.backends.ObjectBackend',
  )

When all configuration is done, bring the database up to date::

  $ ./manage.py migrate bop


Manage permissions
==================

Django-bop provides several mechanisms to manage the permissions for
objects: 

 * bop.admin.ObjectPermissionInline
 * bop.forms.inline_permissions_form_factory
 * An API to grant and revoke permissions to users or groups

More to follow...

.. _article: http://djangoadvent.com/1.2/object-permissions/
.. _other: http://www.djangopackages.com/grids/g/perms/
