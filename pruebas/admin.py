from django import forms
from django.contrib import admin
from django.db.models import Q

from .models import LimiteVertido, Prueba, TipoVertido, referencias_formula


class PruebaAdminForm(forms.ModelForm):
    class Meta:
        model = Prueba
        fields = (
            "codigo",
            "nombre",
            "activa",
            "tipo_calculo",
            "formula",
            "es_calculada",
            "unidad_medicion",
            "unidad",
            "norma",
            "limite_min",
            "limite_max",
            "limite_deteccion",
            "observacion",
        )

    def clean(self):
        datos = super().clean()
        formula = datos.get("formula")
        if formula:
            propio = datos.get("codigo") or self.instance.codigo
            referencias = referencias_formula(formula) - {propio}
            existentes = set(
                Prueba.objects.filter(codigo__in=referencias).values_list("codigo", flat=True)
            )
            for codigo in sorted(referencias - existentes):
                self.add_error(
                    "formula", f"La fórmula referencia «{codigo}», que no existe en el catálogo."
                )
        return datos


class ConObservacionFilter(admin.SimpleListFilter):
    title = "observación"
    parameter_name = "observacion"

    def lookups(self, request, model_admin):
        return (("con", "Con observación"), ("sin", "Sin observación"))

    def queryset(self, request, queryset):
        if self.value() == "con":
            return queryset.filter(~Q(observacion=""))
        if self.value() == "sin":
            return queryset.filter(Q(observacion=""))
        return queryset


class LimiteVertidoInline(admin.TabularInline):
    model = LimiteVertido
    extra = 0
    max_num = len(TipoVertido)
    fields = ("tipo_vertido", "limite_min", "limite_max", "norma")
    verbose_name_plural = "límites por tipo de vertido"


@admin.register(Prueba)
class PruebaAdmin(admin.ModelAdmin):
    form = PruebaAdminForm
    inlines = [LimiteVertidoInline]
    list_display = ("codigo", "nombre", "unidad", "tipo_calculo", "activa")
    list_filter = ("tipo_calculo", "activa", "es_calculada", ConObservacionFilter)
    search_fields = ("codigo", "nombre")
    fieldsets = (
        ("Identificación", {"fields": ("codigo", "nombre", "activa")}),
        (
            "Cálculo",
            {"fields": ("tipo_calculo", "formula", "es_calculada", "unidad_medicion", "unidad")},
        ),
        ("Límites", {"fields": ("norma", "limite_min", "limite_max", "limite_deteccion")}),
        ("Observación", {"fields": ("observacion",)}),
    )

    class Media:
        # Oculta fórmula y "se calcula a partir de otras pruebas" salvo con tipo FORMULA.
        js = ("pruebas/admin_prueba.js",)

    def get_readonly_fields(self, request, obj=None):
        # Una prueba en uso conserva código y nombre: los estudios la muestran así.
        if obj is not None and obj.esta_en_uso():
            return ("codigo", "nombre")
        return ()

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.esta_en_uso():
            return False
        return super().has_delete_permission(request, obj)
