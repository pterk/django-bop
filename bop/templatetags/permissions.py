from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse


register = template.Library()


# Taken from http://bitbucket.org/jezdez/django-authority/src/tip/authority/templatetags/permissions.py
# Made it less flexible ;-)

class ResolverNode(template.Node):
    """
    A small wrapper that adds a convenient resolve method.
    """
    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    @classmethod
    def next_bit_for(cls, bits, key, if_none=None):
        try:
            return bits[bits.index(key)+1]
        except ValueError:
            return if_none


class PermissionComparisonNode(ResolverNode):
    """
    Implements a node to provide an "if user/group has permission on object"
    """
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.contents.split()
        if len(bits) != 4:
            raise template.TemplateSyntaxError(
                "'%s' tag takes four arguments" % bits[0])
        end_tag = 'endifhasperm'
        nodelist_true = parser.parse(('else', end_tag))
        token = parser.next_token()
        if token.contents == 'else': # there is an 'else' clause in the tag
            nodelist_false = parser.parse((end_tag,))
            parser.delete_first_token()
        else:
            nodelist_false = template.NodeList()
        return cls(bits[2], bits[1], nodelist_true, nodelist_false, bits[3])

    def __init__(self, user, perm, nodelist_true, nodelist_false, obj):
        self.user = user
        self.perm = perm
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.obj = obj

    def render(self, context):
        try:
            user = self.resolve(self.user, context)
            perm = self.resolve(self.perm, context)
            obj = self.resolve(self.obj, context)
            if user.has_perm(perm, obj):
                # return True if check was successful
                return self.nodelist_true.render(context)
        # If the app couldn't be found
        except (ImproperlyConfigured, ImportError):
            return ''
        # If either variable fails to resolve, return nothing.
        except template.VariableDoesNotExist:
            return ''
        # If the types don't permit comparison, return nothing.
        except (TypeError, AttributeError):
            return ''
        return self.nodelist_false.render(context)

@register.tag
def ifhasperm(parser, token):
    """
    This function provides functionality for the 'ifhasperm' template tag

    Syntax::

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

    """
    return PermissionComparisonNode.handle_token(parser, token)

