from django.contrib import admin
from django.utils.html import format_html

from .models import FirmaProfesional

# Informe y EnvioInforme no tienen admin: son inalterables (US 7.3 y SCRUM-79).


@admin.register(FirmaProfesional)
class FirmaProfesionalAdmin(admin.ModelAdmin):
    """Corrección de la matrícula (SCRUM-81): el bioquímico la escribe una sola vez en Mi firma.

    Solo se cambia la matrícula. La firma la dibuja cada uno y no se crea ni se borra desde acá.
    Los informes ya emitidos conservan la copia con la que salieron.
    """

    list_display = ("usuario", "matricula", "actualizada")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name", "matricula")
    fields = ("usuario", "vista_firma", "matricula", "actualizada")
    readonly_fields = ("usuario", "vista_firma", "actualizada")

    @admin.display(description="firma")
    def vista_firma(self, obj):
        return format_html(
            '<img src="{}" alt="Firma" style="max-height:80px;background:#fff">', obj.data_url
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
