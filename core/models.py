"""
Modelos corregidos - Sistema de trazabilidad
CAMBIOS CRÍTICOS:
1. Agregado campo 'direccion' a Madre
2. Corregido manejo de epicrisis_data
3. Mejorada validación de correcciones
"""

from django.db import models
from django.conf import settings
import uuid
from utils.crypto import crypto_service


class Madre(models.Model):
    """
    Modelo de Madre con datos sensibles cifrados
    NUEVO: Campo direccion agregado
    """
    PREVISION_CHOICES = [
        ('FONASA', 'FONASA'),
        ('ISAPRE', 'ISAPRE'),
        ('PARTICULAR', 'PARTICULAR'),
        ('NINGUNA', 'Ninguna'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CORREGIDO: ficha_clinica_id ahora es para ID, no dirección
    ficha_clinica_id = models.CharField(max_length=255, unique=True, null=True, blank=True, 
                                       verbose_name="Número de Ficha Clínica")
    
    # NUEVO: Campo para dirección
    direccion = models.TextField(null=True, blank=True, verbose_name="Dirección de Residencia")
    
    # Datos cifrados + hash para búsqueda
    rut_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    rut_encrypted = models.TextField(null=True, blank=True)
    nombre_hash = models.CharField(max_length=255, null=True, blank=True)
    nombre_encrypted = models.TextField(null=True, blank=True)
    telefono_hash = models.CharField(max_length=255, null=True, blank=True)
    telefono_encrypted = models.TextField(null=True, blank=True)
    
    # Datos no sensibles
    fecha_nacimiento = models.DateField()
    nacionalidad = models.CharField(max_length=100, null=True, blank=True)
    pertenece_pueblo_originario = models.BooleanField(default=False)
    prevision = models.CharField(max_length=50, choices=PREVISION_CHOICES, null=True, blank=True)
    antecedentes_medicos = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Madre'
        verbose_name = 'Madre'
        verbose_name_plural = 'Madres'
    
    def __str__(self):
        nombre = self.get_nombre()
        return f"Madre - {nombre if nombre else self.ficha_clinica_id}"
    
    # Métodos de cifrado (sin cambios)
    def set_rut(self, rut):
        self.rut_encrypted = crypto_service.encrypt(rut)
        self.rut_hash = crypto_service.hash_data(rut)
    
    def get_rut(self):
        return crypto_service.decrypt(self.rut_encrypted) if self.rut_encrypted else None
    
    def set_nombre(self, nombre):
        self.nombre_encrypted = crypto_service.encrypt(nombre)
        self.nombre_hash = crypto_service.hash_data(nombre)
    
    def get_nombre(self):
        return crypto_service.decrypt(self.nombre_encrypted) if self.nombre_encrypted else None
    
    def set_telefono(self, telefono):
        self.telefono_encrypted = crypto_service.encrypt(telefono)
        self.telefono_hash = crypto_service.hash_data(telefono)
    
    def get_telefono(self):
        return crypto_service.decrypt(self.telefono_encrypted) if self.telefono_encrypted else None


class DiagnosticoCIE10(models.Model):
    """Modelo de diagnósticos CIE-10"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField()
    
    class Meta:
        db_table = 'DiagnosticoCIE10'
        verbose_name = 'Diagnóstico CIE-10'
        verbose_name_plural = 'Diagnósticos CIE-10'
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class Parto(models.Model):
    """
    Modelo de Parto con datos clínicos
    CORREGIDO: Validación de epicrisis_data
    """
    TIPO_PARTO_CHOICES = [
        ('Eutócico', 'Eutócico'),
        ('Cesárea Electiva', 'Cesárea Electiva'),
        ('Cesárea Urgencia', 'Cesárea Urgencia'),
        ('Fórceps', 'Fórceps'),
        ('Ventosa', 'Ventosa'),
    ]
    
    ANESTESIA_CHOICES = [
        ('Epidural', 'Epidural'),
        ('Raquídea', 'Raquídea'),
        ('General', 'General'),
        ('Otra', 'Otra'),
        ('Ninguna', 'Ninguna'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    madre = models.ForeignKey(Madre, on_delete=models.PROTECT, related_name='partos')
    fecha_parto = models.DateTimeField()
    edad_gestacional = models.IntegerField(null=True, blank=True)
    tipo_parto = models.CharField(max_length=50, choices=TIPO_PARTO_CHOICES)
    anestesia = models.CharField(max_length=50, choices=ANESTESIA_CHOICES, null=True, blank=True)
    
    # Datos clínicos en formato JSON
    partograma_data = models.JSONField(null=True, blank=True)
    epicrisis_data = models.JSONField(null=True, blank=True)
    
    # Relación con diagnósticos
    diagnosticos = models.ManyToManyField(DiagnosticoCIE10, through='PartoDiagnostico')
    
    # Auditoría
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='partos_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Parto'
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'
        ordering = ['-fecha_parto']
    
    def __str__(self):
        return f"Parto {self.tipo_parto} - {self.fecha_parto.strftime('%d/%m/%Y')}"
    
    # NUEVO: Método para validar epicrisis completa
    def tiene_epicrisis(self):
        """Verifica si el parto tiene epicrisis registrada"""
        return self.epicrisis_data is not None and len(self.epicrisis_data) > 0
    
    # NUEVO: Método para obtener indicaciones
    def get_indicaciones(self):
        """Retorna las indicaciones médicas del parto"""
        return self.indicaciones.all()


class PartoDiagnostico(models.Model):
    """Tabla intermedia para relación Parto-Diagnóstico"""
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE)
    diagnostico = models.ForeignKey(DiagnosticoCIE10, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'PartoDiagnostico'
        unique_together = ('parto', 'diagnostico')


class RecienNacido(models.Model):
    """Modelo de Recién Nacido (sin cambios necesarios)"""
    ESTADO_CHOICES = [
        ('Vivo', 'Vivo'),
        ('Nacido Muerto', 'Nacido Muerto'),
    ]
    
    SEXO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Indeterminado', 'Indeterminado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='recien_nacidos')
    rut_provisorio = models.CharField(max_length=255, null=True, blank=True)
    estado_al_nacer = models.CharField(max_length=50, choices=ESTADO_CHOICES)
    sexo = models.CharField(max_length=50, choices=SEXO_CHOICES, null=True, blank=True)
    
    # Datos antropométricos
    peso_gramos = models.IntegerField(null=True, blank=True)
    talla_cm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Evaluación APGAR
    apgar_1_min = models.SmallIntegerField(null=True, blank=True)
    apgar_5_min = models.SmallIntegerField(null=True, blank=True)
    
    # Profilaxis
    profilaxis_vit_k = models.BooleanField(default=False)
    profilaxis_oftalmica = models.BooleanField(default=False)
    
    # Auditoría
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recien_nacidos_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'RecienNacido'
        verbose_name = 'Recién Nacido'
        verbose_name_plural = 'Recién Nacidos'
    
    def __str__(self):
        return f"RN - {self.sexo} - {self.estado_al_nacer}"


class Correccion(models.Model):
    """
    Modelo de Correcciones
    CORREGIDO: Validación de permisos en el modelo
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.PROTECT, related_name='correcciones')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='correcciones_realizadas'
    )
    fecha_correccion = models.DateTimeField(auto_now_add=True)

    CAMPO_CHOICES = [
        ('tipo_parto', 'Tipo de Parto'),
        ('peso_gramos', 'Peso RN (g)'),
        ('talla_cm', 'Talla RN (cm)'),
        ('apgar_1_min', 'APGAR 1 min'),
        ('apgar_5_min', 'APGAR 5 min'),
        ('observaciones', 'Observaciones'),
        ('otro', 'Otro'),
    ]
    campo_corregido = models.CharField(max_length=100, choices=CAMPO_CHOICES)
    valor_original = models.TextField(blank=True)
    valor_nuevo = models.TextField()
    justificacion = models.TextField()

    class Meta:
        db_table = 'Correccion'
        ordering = ['-fecha_correccion']
        verbose_name = 'Corrección de Registro'
        verbose_name_plural = 'Correcciones de Registros'

    def __str__(self):
        return f"Corrección en {self.parto_id} por {self.usuario.username}"
    
    # NUEVO: Método de validación
    def save(self, *args, **kwargs):
        """Valida que el usuario tenga permisos antes de guardar"""
        if not self.usuario.puede_anexar_correccion:
            raise PermissionError("Usuario sin permisos para anexar correcciones")
        super().save(*args, **kwargs)


class Indicacion(models.Model):
    """Modelo de Indicaciones Médicas (sin cambios necesarios)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='indicaciones')

    TIPO_CHOICES = [
        ('medicamento', 'Medicamento'),
        ('procedimiento', 'Procedimiento'),
        ('cuidado', 'Cuidado de Enfermería'),
        ('dieta', 'Dieta'),
        ('reposo', 'Reposo'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=255)
    dosis = models.CharField(max_length=100, blank=True, null=True)
    via = models.CharField(max_length=100, blank=True, null=True)
    frecuencia = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'Indicacion'
        ordering = ['-parto__fecha_parto']

    def __str__(self):
        return f"Indicación ({self.tipo}) para Parto {self.parto.id}"


class Defuncion(models.Model):
    """Modelo de Defunción (sin cambios necesarios)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recien_nacido = models.OneToOneField(
        RecienNacido,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='defuncion'
    )
    madre = models.OneToOneField(
        Madre,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='defuncion'
    )
    fecha_defuncion = models.DateTimeField()
    causa_defuncion = models.ForeignKey(DiagnosticoCIE10, on_delete=models.PROTECT)
    
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='defunciones_registradas'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Defuncion'
        verbose_name = 'Defunción'
        verbose_name_plural = 'Defunciones'
        constraints = [
            models.CheckConstraint(
                check=models.Q(recien_nacido__isnull=False) | models.Q(madre__isnull=False),
                name='defuncion_recien_nacido_o_madre'
            )
        ]
    
    def __str__(self):
        if self.recien_nacido:
            return f"Defunción RN - {self.fecha_defuncion.strftime('%d/%m/%Y')}"
        else:
            return f"Defunción Madre - {self.fecha_defuncion.strftime('%d/%m/%Y')}"


class DocumentoReferencia(models.Model):
    """Modelo para referenciar documentos en MongoDB"""
    TIPO_DOCUMENTO_CHOICES = [
        ('EPICRISIS_PDF', 'Epicrisis PDF'),
        ('REPORTE_EXCEL', 'Reporte Excel'),
        ('OTRO', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='documentos')
    mongodb_object_id = models.CharField(max_length=255, unique=True)
    nombre_archivo = models.TextField()
    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES)
    
    usuario_generacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documentos_generados'
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'DocumentoReferencia'
        verbose_name = 'Documento de Referencia'
        verbose_name_plural = 'Documentos de Referencia'
    
    def __str__(self):
        return f"{self.nombre_archivo} - {self.tipo_documento}"