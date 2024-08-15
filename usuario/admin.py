from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # Optional: Customize how the user is displayed in the admin
    list_display = ('username', 'email', 'nombreCompleto', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'nombreCompleto')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nombreCompleto', 'fotoDePerfil')}),
    )

# admin.site.register(Usuario, CustomUserAdmin)  # Alternatively, use this line without the decorator