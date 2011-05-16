from django.contrib.auth.models import Permission
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.contrib.contenttypes.models import ContentType
from django import forms

from bop.models import ObjectPermission


def inline_permissions_form_factory(model, extra=1):
    """ Returns a modelformset for ObjectPermission linked to <model>

    InlinePermissionForm = inline_permissions_form_factory(MyModel)
    # myobject is an instance of MyModel
    form = MyModelForm(instance=myobject) 
    formset = InlinePermissionForm(instance=myobject)
    """
    def formfield_callback(field, *args):
        ct = ContentType.objects.get_for_model(model)
        if field.name == 'permission':
            return field.formfield(
                queryset=Permission.objects.filter(content_type=ct))
        return field.formfield()
    return generic_inlineformset_factory(
        ObjectPermission, extra=extra, formfield_callback=formfield_callback)
