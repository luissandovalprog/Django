"""
Configuración del Admin de Django para Core
"""

from django.contrib import admin
from .models import Madre, Parto, RecienNacido, DiagnosticoCIE10, Defuncion, DocumentoReferencia


@admin.register(Madre)
class MadreAdmin(admin.ModelAdmin):
    list_display = ('ficha_clinica_id', 'fecha_nacimiento', 'prevision', 'fecha_registro')
    list_filter = ('prevision', 'pertenece_pueblo_originario')
    search_fields = ('ficha_clinica_id',)
    readonly_fields = ('fecha_registro',)
    
    def get_nombre(self, obj):
        return obj.get_nombre()
    get_nombre.short_description = 'Nombre'


@admin.register(DiagnosticoCIE10)
class DiagnosticoCIE10Admin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion')
    search_fields = ('codigo', 'descripcion')


@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    list_display = ('fecha_parto', 'madre', 'tipo_parto', 'anestesia', 'usuario_registro')
    list_filter = ('tipo_parto', 'anestesia')
    search_fields = ('madre__ficha_clinica_id',)
    readonly_fields = ('fecha_registro',)
    date_hierarchy = 'fecha_parto'


@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    list_display = ('parto', 'estado_al_nacer', 'sexo', 'peso_gramos', 'talla_cm', 'apgar_5_min')
    list_filter = ('estado_al_nacer', 'sexo')
    readonly_fields = ('fecha_registro',)


@admin.register(Defuncion)
class DefuncionAdmin(admin.ModelAdmin):
    list_display = ('fecha_defuncion', 'recien_nacido', 'madre', 'causa_defuncion')
    list_filter = ('fecha_defuncion',)
    readonly_fields = ('fecha_registro',)


@admin.register(DocumentoReferencia)
class DocumentoReferenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'tipo_documento', 'parto', 'fecha_generacion')
    list_filter = ('tipo_documento',)
    readonly_fields = ('fecha_generacion',)
