from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes import generic 
from django.contrib.contenttypes.models import ContentType

from bop.models import ObjectPermission


class ObjectPermissionInline(generic.GenericTabularInline):
    """ Generates the inline ObjectPermissions form for the 'related'
    model (with only the relevant permissions)

    """
    model = ObjectPermission
    extra = 1

    # Need to override this entire method to pass a different
    # formfield_callback :-(
    def get_formset(self, request, obj=None):
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(self.get_readonly_fields(request, obj))
        exclude = exclude or None

        def _formfield_callback(field, *args):
            if field.name == 'permission':
                ct = ContentType.objects.get_for_model(self.parent_model)
                return field.formfield(
                    queryset=Permission.objects.filter(content_type=ct))
            return field.formfield()

        defaults = {
            "ct_field": self.ct_field,
            "fk_field": self.ct_fk_field,
            "form": self.form,
            "formfield_callback": _formfield_callback,
            "formset": self.formset,
            "extra": self.extra,
            "can_delete": self.can_delete,
            "can_order": False,
            "fields": fields,
            "max_num": self.max_num,
            "exclude": exclude
        }
        return generic.generic_inlineformset_factory(self.model, **defaults)


class ObjectAdmin(admin.ModelAdmin):
    """ Object Level Permissions in the admin

    """
    def __init__(self, *args, **kwargs):
        super(ObjectAdmin, self).__init__(*args, **kwargs)
        inline_instance = ObjectPermissionInline(self.model, self.admin_site)
        self.inline_instances.append(inline_instance)

    def queryset(self, request):
        opts = self.opts
        queryset = super(ObjectAdmin, self).queryset(request)
        if request.user.is_superuser:
            return queryset
        allowed_ids = ObjectPermission.objects.get_for_model_and_user(
            self.model, request.user).filter(
            permission__codename__in=(
                    opts.get_change_permission(),
                    opts.get_delete_permission()
                    )
            ).values_list('object_id', flat=True).distinct()
        return queryset.filter(id__in=allowed_ids)

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission(), obj)

    def has_delete_permission(self, request, obj=None):
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_delete_permission(), obj)
