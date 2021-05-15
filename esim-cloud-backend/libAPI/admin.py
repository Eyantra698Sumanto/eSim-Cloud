from django.contrib import admin, messages
from libAPI.models import LibraryComponent, Library, LibrarySet, save_libs
from .forms import LibrarySetForm
from inline_actions.admin import InlineActionsMixin
from inline_actions.admin import InlineActionsModelAdminMixin
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from esimCloud import settings
import os


@admin.register(LibraryComponent)
class LibraryComponentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'image_tag', 'svg_path', 'keyword',
                    'description')
    list_filter = ('symbol_prefix', 'component_library__library_name')
    search_fields = ('keyword', 'name')


class ComponentInline(admin.TabularInline):
    model = LibraryComponent
    extra = 1


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    inlines = (ComponentInline, )


class LibraryInline(InlineActionsMixin, admin.TabularInline):
    model = Library
    extra = 0
    show_change_link = True
    inline_actions = ['toggle_default']

    def toggle_default(self, request, obj, parent_obj=None):
        try:
            library_set = LibrarySet.objects.filter(
                user=parent_obj.user,
                default=True if parent_obj.default == False else False
            )[0]
        except IndexError:
            print("Creating new one")
            library_set = LibrarySet(
                name=parent_obj.user.username[0:15] + "-eSim-def",
                default=(True if parent_obj.default == False else False),
                user=parent_obj.user
            )
            library_set.save()
        msg = "removed from" if parent_obj.default == True else "added to"
        messages.info(request, mark_safe(
            f"Library {obj.library_name} {msg} <a href='/api/admin/libAPI/libraryset/{library_set.id}'>{library_set.name}</a>."))
        obj.library_set = library_set
        obj.save()
        # return redirect('/api/admin/libAPI/libraryset/' + str(library_set.id))

    def get_toggle_default_label(self, obj):
        if obj.library_set.default == True:
            return 'Remove from Defaults'
        return 'Add to Defaults'


class LibrarySetAdmin(InlineActionsModelAdminMixin, admin.ModelAdmin):
    model = LibrarySet
    list_display = ('name', 'user', 'default')
    inlines = (LibraryInline, )

    def get_form(self, request, obj=None, **kwargs):
        return LibrarySetForm

    def save_model(self, request, obj, form, change):
        # For new library set instance
        if obj.pk is None:
            obj = LibrarySet(
                user=request.user,
                default=True if request.POST.get('default') else False,
                name=request.POST.get('name', '')[0:24]
            )
            obj.save()

        # If the library set is being changed
        else:
            obj.save()

        files = request.FILES.getlist('files')
        if len(files) != 0:
            path = os.path.join(
                settings.BASE_DIR,
                'kicad-symbols',
                request.user.username + '-' + request.POST.get('name', ''))

            save_libs(obj, path, files)  # defined in ./models.py
        return redirect('/api/admin/libAPI/libraryset/' + str(obj.id))


admin.site.register(LibrarySet, LibrarySetAdmin)
