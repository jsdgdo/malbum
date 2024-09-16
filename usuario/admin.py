from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError, transaction
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # Optional: Customize how the user is displayed in the admin
    list_display = ('username', 'email', 'nombreCompleto', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'nombreCompleto')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

    def save_model(self, request, obj, form, change):
        try: 
            with transaction.atomic():
                obj.save()
        except IntegrityError as e:
            self.message_user(request, f"Error al guardar el usuario: {str(e)}", level=self.message_level)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nombreCompleto', 'fotoDePerfil')}),
    )

    def save_related(self, request, form, formsets, change):
        """Override save_related to handle ManyToMany fields safely."""
        try:
            with transaction.atomic():
                super().save_related(request, form, formsets, change)
        except IntegrityError as e:
            self.message_user(request, f"Error saving related objects: {str(e)}", level='error')

# admin.site.register(Usuario, CustomUserAdmin)  # Alternatively, use this line without the decorator