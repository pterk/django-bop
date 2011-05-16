try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.utils.http import urlquote


# closely matches user
def user_has_object_level_perm(perm, model=None, pkfield='pk', login_url=None,
                               redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user has `perm` on `obj`
    (from model with pk) redirecting to the log-in page if necessary.

    Model should be a model class and pkfield the name of the primary
    key that is passed as a kwarg to the view.
    """
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            obj = model.objects.get(pk=kwargs[pkfield])
            if request.user.has_perm(perm, obj):
                return view_func(request, *args, **kwargs)
            path = urlquote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            return HttpResponseRedirect('%s?%s=%s' % tup)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator
