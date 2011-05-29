Installation
============

Install django-bop in your (virtual) environment::

  $ pip install django-bop

If you haven't already you should also install south::

  $ pip install South

Add 'bop' (and south) to you INSTALLED_APPS in settings.py::

  INSTALLED_APPS = (
    ...
    'south',
    'bop',
  )

While in settings.py specify the AUTHENTICATION_BACKENDS::

  AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'bop.backends.ObjectBackend',
  )

If you, optionally, want to give permissions to anonymous users you
should do the following:

1. Add a user to contrib.auth.models.User to represent anonymous users
   (e.g. via the admin). Give it an appropriate name (anon /
   anonymous) so it easily recognized when assigning permissions.

2. Add ANONYMOUS_USER_ID to settings.py::

     ANONYMOUS_USER_ID = 2

If, in addition -- and again optionally -- you want to support
Model-permissions for anonymous users, you can add the
AnonymousModelBackend::

  AUTHENTICATION_BACKENDS = (
      'django.contrib.auth.backends.ModelBackend',
      'bop.backends.AnonymousModelBackend',
      'bop.backends.ObjectBackend',
  )

When all configuration is done, bring the database up to date::

  $ ./manage.py migrate bop

