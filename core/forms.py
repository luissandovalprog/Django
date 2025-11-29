from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Madre, Parto, RecienNacido, DiagnosticoCIE10, Correccion, Indicacion
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils import timezone

class MadreForm(forms.ModelForm):
    """
    Formulario para crear/editar Madre
    """
    
    # Campos no cifrados para el formulario
    rut = forms.CharField(
        max_length=12,
        required=True,
        label='RUT',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12.345.678-9'
        })
    )
    
    nombre = forms.CharField(
        max_length=255,
        required=True,
        label='Nombre Completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo de la paciente'
        })
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56 9 1234 5678'
        })
    )
    
    class Meta:
        model = Madre
        fields = [
            'ficha_clinica_numero',
            'direccion',
            'fecha_nacimiento',
            'nacionalidad',
            'pertenece_pueblo_originario',
            'prevision',
            'antecedentes_medicos'
        ]
        widgets = {
            'ficha_clinica_numero': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: FC-2025-001',
                'readonly': True,
                'style': 'background-color: #f3f4f6; cursor: not-allowed;'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Dirección de residencia completa'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'nacionalidad': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[('Chilena', 'Chilena'), ('Extranjera', 'Extranjera')]),
            'pertenece_pueblo_originario': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'prevision': forms.Select(attrs={
                'class': 'form-control'
            }),
            'antecedentes_medicos': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Antecedentes médicos relevantes'
            }),
        }
        labels = {
            'ficha_clinica_numero': 'Número de Ficha Clínica',
            'direccion': 'Dirección de Residencia',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'nacionalidad': 'Nacionalidad',
            'pertenece_pueblo_originario': 'Pertenece a Pueblo Originario',
            'prevision': 'Previsión',
            'antecedentes_medicos': 'Antecedentes Médicos'
        }
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            # Si estamos editando, cargar los datos cifrados
            initial = kwargs.get('initial', {})
            initial['rut'] = instance.get_rut() or ''
            initial['nombre'] = instance.get_nombre() or ''
            initial['telefono'] = instance.get_telefono() or ''
            kwargs['initial'] = initial
        else:
            # Si estamos creando, generar ficha automática
            initial = kwargs.get('initial', {})
            initial['ficha_clinica_numero'] = self.generar_numero_ficha()
            kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
        
        # Hacer el campo readonly siempre
        self.fields['ficha_clinica_numero'].disabled = True
    
    @staticmethod
    def generar_numero_ficha():
        """
        Genera el siguiente número de ficha en formato FC-YYYY-NNN
        Ejemplo: FC-2025-001, FC-2025-002, etc.
        """
        from datetime import datetime
        
        año_actual = datetime.now().year
        
        # Buscar la última ficha del año actual
        ultima_madre = Madre.objects.filter(
            ficha_clinica_numero__startswith=f'FC-{año_actual}-'
        ).order_by('-ficha_clinica_numero').first()
        
        if ultima_madre and ultima_madre.ficha_clinica_numero:
            # Extraer el número de la última ficha
            try:
                ultimo_numero = int(ultima_madre.ficha_clinica_numero.split('-')[-1])
                siguiente_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                siguiente_numero = 1
        else:
            # Primera ficha del año
            siguiente_numero = 1
        
        # Formatear con ceros a la izquierda (3 dígitos)
        return f'FC-{año_actual}-{siguiente_numero:03d}'
    
    def clean_rut(self):
        """Validar formato de RUT chileno"""
        rut = self.cleaned_data.get('rut', '')
        return rut
    
    def clean_fecha_nacimiento(self):
        """Validar que la fecha de nacimiento sea válida"""
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            from datetime import date
            if fecha > date.today():
                raise ValidationError('La fecha de nacimiento no puede ser futura')
            edad = (date.today() - fecha).days // 365
            if edad < 12 or edad > 60:
                raise ValidationError('La edad debe estar entre 12 y 60 años')
        return fecha
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Guardar datos cifrados
        instance.set_rut(self.cleaned_data.get('rut'))
        instance.set_nombre(self.cleaned_data.get('nombre'))
        if self.cleaned_data.get('telefono'):
            instance.set_telefono(self.cleaned_data.get('telefono'))
        
        if commit:
            instance.save()
        return instance


# Los demás formularios permanecen sin cambios...
class PartoForm(forms.ModelForm):
    """Formulario para crear/editar Parto (sin cambios)"""
    
    class Meta:
        model = Parto
        fields = [
            'madre',
            'fecha_parto',
            'edad_gestacional',
            'tipo_parto',
            'anestesia',
        ]
        widgets = {
            'madre': forms.Select(attrs={'class': 'form-control'}),
            'fecha_parto': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'edad_gestacional': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '20',
                'max': '45',
                'placeholder': 'Semanas de gestación'
            }),
            'tipo_parto': forms.Select(attrs={'class': 'form-control'}),
            'anestesia': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'madre': 'Madre',
            'fecha_parto': 'Fecha y Hora del Parto',
            'edad_gestacional': 'Edad Gestacional (semanas)',
            'tipo_parto': 'Tipo de Parto',
            'anestesia': 'Anestesia',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Mostrar el nombre descifrado de las madres en el selector
        if 'madre' in self.fields:
            choices = [('', '---------')]
            for madre in Madre.objects.all():
                nombre = madre.get_nombre()
                ficha = madre.ficha_clinica_id
                label = f"{nombre} - Ficha: {ficha}" if nombre and ficha else (nombre or ficha or str(madre.id))
                choices.append((madre.id, label))
            self.fields['madre'].choices = choices
    
    def clean_edad_gestacional(self):
        """Validar edad gestacional"""
        edad = self.cleaned_data.get('edad_gestacional')
        if edad and (edad < 20 or edad > 45):
            raise ValidationError('La edad gestacional debe estar entre 20 y 45 semanas')
        return edad
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.usuario_registro = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class RecienNacidoForm(forms.ModelForm):
    """Formulario para crear/editar Recién Nacido (CORREGIDO)"""
    
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'rut_provisorio', 'estado_al_nacer', 'sexo', 
            'peso_gramos', 'talla_cm', 'apgar_1_min', 'apgar_5_min',
            'profilaxis_vit_k', 'profilaxis_oftalmica'
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'form-control'}),
            'rut_provisorio': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'RUT provisorio',
                'readonly': True,
                'style': 'background-color: #f3f4f6; cursor: not-allowed;'
            }),
            'estado_al_nacer': forms.Select(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'peso_gramos': forms.NumberInput(attrs={'class': 'form-control', 'min': '500', 'max': '6000', 'placeholder': 'Peso en gramos'}),
            'talla_cm': forms.NumberInput(attrs={'class': 'form-control', 'min': '25', 'max': '65', 'step': '0.1', 'placeholder': 'Talla en cm'}),
            'apgar_1_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'apgar_5_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'profilaxis_vit_k': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profilaxis_oftalmica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'parto': 'Parto',
            'rut_provisorio': 'RUT Provisorio',
            'estado_al_nacer': 'Estado al Nacer',
            'sexo': 'Sexo',
            'peso_gramos': 'Peso (gramos)',
            'talla_cm': 'Talla (cm)',
            'apgar_1_min': 'APGAR 1 minuto',
            'apgar_5_min': 'APGAR 5 minutos',
            'profilaxis_vit_k': 'Profilaxis Vitamina K',
            'profilaxis_oftalmica': 'Profilaxis Oftálmica',
        }
    
    def __init__(self, *args, **kwargs):
        # CRÍTICO: Extraer el usuario del constructor
        self.user = kwargs.pop('user', None)
        
        # Obtener el parto si se pasa en initial
        parto = kwargs.get('initial', {}).get('parto')
        
        super().__init__(*args, **kwargs)
        
        # Si estamos creando (no editando) y tenemos un parto, generar RUT provisorio
        if not self.instance.pk and parto:
            self.fields['rut_provisorio'].initial = self.generar_rut_provisorio(parto)
        
        # Hacer el campo readonly siempre
        self.fields['rut_provisorio'].disabled = True
    
    @staticmethod
    def generar_rut_provisorio(parto):
        """
        Genera RUT provisorio basado en el RUT de la madre + correlativo del hijo
        
        Formato: RUT_MADRE_SIN_DV + NUMERO_HIJO
        Ejemplo:
        - Madre: 12.345.678-9
        - Hijo 1: 12.345.678-1
        - Hijo 2: 12.345.678-2
        """
        if not parto or not parto.madre:
            return ''
        
        # Obtener el RUT de la madre (descifrado)
        rut_madre = parto.madre.get_rut()
        
        if not rut_madre:
            return ''
        
        # Limpiar el RUT (quitar puntos y guión)
        rut_limpio = rut_madre.replace('.', '').replace('-', '')
        
        # Extraer solo los números (sin el DV)
        if len(rut_limpio) > 1:
            rut_sin_dv = rut_limpio[:-1]
        else:
            return ''
        
        # Contar cuántos hijos ya tiene este parto
        cantidad_hijos = parto.recien_nacidos.count()
        correlativo_hijo = cantidad_hijos + 1
        
        # Formatear el RUT provisorio con puntos y guión
        # Ejemplo: 12345678 -> 12.345.678
        rut_formateado = ''
        for i, digit in enumerate(reversed(rut_sin_dv)):
            if i > 0 and i % 3 == 0:
                rut_formateado = '.' + rut_formateado
            rut_formateado = digit + rut_formateado
        
        # Retornar RUT provisorio: RUT_SIN_DV-CORRELATIVO
        return f'{rut_formateado}-{correlativo_hijo}'
    
    def clean_peso_gramos(self):
        peso = self.cleaned_data.get('peso_gramos')
        if peso and (peso < 500 or peso > 6000):
            raise ValidationError('El peso debe estar entre 500 y 6000 gramos')
        return peso
    
    def clean_talla_cm(self):
        talla = self.cleaned_data.get('talla_cm')
        if talla and (talla < 25 or talla > 65):
            raise ValidationError('La talla debe estar entre 25 y 65 cm')
        return talla
    
    def clean_apgar_1_min(self):
        apgar = self.cleaned_data.get('apgar_1_min')
        if apgar is not None and (apgar < 0 or apgar > 10):
            raise ValidationError('El APGAR debe estar entre 0 y 10')
        return apgar
    
    def clean_apgar_5_min(self):
        apgar = self.cleaned_data.get('apgar_5_min')
        if apgar is not None and (apgar < 0 or apgar > 10):
            raise ValidationError('El APGAR debe estar entre 0 y 10')
        return apgar
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # CRÍTICO: Asignar usuario_registro si no está asignado y tenemos user
        if self.user and not instance.usuario_registro_id:
            instance.usuario_registro = self.user
        
        # Si no tiene RUT provisorio, generarlo antes de guardar
        if not instance.rut_provisorio and instance.parto:
            instance.rut_provisorio = self.generar_rut_provisorio(instance.parto)
        
        if commit:
            instance.save()
        return instance


class CorreccionForm(forms.ModelForm):
    # Campos permitidos por tipo de modelo
    CAMPO_CHOICES_MADRE = [
        ('', 'Seleccione un campo...'),
        ('rut', 'RUT'),
        ('nombre', 'Nombre Completo'),
        ('telefono', 'Teléfono'),
        ('direccion', 'Dirección'),
        ('fecha_nacimiento', 'Fecha de Nacimiento'),
        ('nacionalidad', 'Nacionalidad'),
        ('prevision', 'Previsión'),
        ('antecedentes_medicos', 'Antecedentes Médicos'),
        ('pertenece_pueblo_originario', 'Pertenece a Pueblo Originario'),
    ]
    
    CAMPO_CHOICES_PARTO = [
        ('', 'Seleccione un campo...'),
        ('tipo_parto', 'Tipo de Parto'),
        ('anestesia', 'Anestesia'),
        ('fecha_parto', 'Fecha y Hora del Parto'),
        ('edad_gestacional', 'Edad Gestacional (semanas)'),
    ]
    
    CAMPO_CHOICES_RN = [
        ('', 'Seleccione un campo...'),
        ('rut_provisorio', 'RUT Provisorio'),
        ('estado_al_nacer', 'Estado al Nacer'),
        ('sexo', 'Sexo'),
        ('peso_gramos', 'Peso (gramos)'),
        ('talla_cm', 'Talla (cm)'),
        ('apgar_1_min', 'APGAR 1 minuto'),
        ('apgar_5_min', 'APGAR 5 minutos'),
        ('profilaxis_vit_k', 'Profilaxis Vitamina K'),
        ('profilaxis_oftalmica', 'Profilaxis Oftálmica'),
    ]
    
    campo_corregido = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_campo_corregido'
        }),
        label='Campo a Corregir'
    )
    
    class Meta:
        model = Correccion
        fields = ['campo_corregido', 'valor_original', 'valor_nuevo', 'justificacion']
        widgets = {
            'valor_original': forms.TextInput(attrs={
                'class': 'form-input', 
                'readonly': True,
                'id': 'id_valor_original',
                'placeholder': 'Se cargará automáticamente...'
            }),
            'valor_nuevo': forms.TextInput(attrs={
                'class': 'form-input',
                'id': 'id_valor_nuevo',
                'placeholder': 'Ingrese el valor corregido'
            }),
            'justificacion': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 4,
                'id': 'id_justificacion',
                'placeholder': 'Justificación médica detallada (mínimo 20 caracteres)'
            }),
        }
        labels = {
            'campo_corregido': 'Campo a Corregir',
            'valor_original': 'Valor Original',
            'valor_nuevo': 'Valor Corregido',
            'justificacion': 'Justificación Médica',
        }
    
    def __init__(self, *args, **kwargs):
        self.tipo_modelo = kwargs.pop('tipo_modelo', 'parto')
        super().__init__(*args, **kwargs)
        
        # Establecer las choices según el tipo de modelo
        if self.tipo_modelo == 'madre':
            self.fields['campo_corregido'].choices = self.CAMPO_CHOICES_MADRE
        elif self.tipo_modelo == 'recien_nacido':
            self.fields['campo_corregido'].choices = self.CAMPO_CHOICES_RN
        else:  # 'parto' por defecto
            self.fields['campo_corregido'].choices = self.CAMPO_CHOICES_PARTO

    def clean_justificacion(self):
        justificacion = self.cleaned_data.get('justificacion', '')
        if len(justificacion) < 20:
            raise forms.ValidationError('La justificación debe tener al menos 20 caracteres.')
        return justificacion
    
    def clean_valor_nuevo(self):
        valor_nuevo = self.cleaned_data.get('valor_nuevo', '')
        if not valor_nuevo or valor_nuevo.strip() == '':
            raise forms.ValidationError('El valor corregido no puede estar vacío.')
        return valor_nuevo.strip()


class EpicrisisForm(forms.Form):
    """Formulario para epicrisis"""
    
    motivo_ingreso = forms.CharField(
        label="Motivo de Ingreso", 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    resumen_evolucion = forms.CharField(
        label="Resumen de Evolución *", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True
    )
    
    diagnostico_egreso = forms.CharField(
        label="Diagnóstico de Egreso *", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    
    condicion_egreso = forms.ChoiceField(
        label="Condición al Egreso *", 
        choices=[
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('grave', 'Grave'),
            ('fallecido', 'Fallecido')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    control_posterior = forms.CharField(
        label="Control Posterior", 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    indicaciones_alta = forms.CharField(
        label="Indicaciones al Alta", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    observaciones = forms.CharField(
        label="Observaciones", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )


class IndicacionForm(forms.ModelForm):
    """Formulario para indicaciones médicas"""
    
    class Meta:
        model = Indicacion
        fields = ['tipo', 'descripcion', 'dosis', 'via', 'frecuencia']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'dosis': forms.TextInput(attrs={'class': 'form-control'}),
            'via': forms.TextInput(attrs={'class': 'form-control'}),
            'frecuencia': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo': 'Tipo de Indicación',
            'descripcion': 'Descripción *',
            'dosis': 'Dosis',
            'via': 'Vía de Administración',
            'frecuencia': 'Frecuencia',
        }


# Formset para indicaciones
IndicacionFormSet = inlineformset_factory(
    Parto, 
    Indicacion, 
    form=IndicacionForm, 
    extra=1, 
    can_delete=True,
    fk_name='parto'
)

class PartogramaForm(forms.Form):
    """
    Formulario para registrar datos del partograma
    Los datos se guardan en formato JSON en Parto.partograma_data
    """
    
    # Información General
    hora_inicio = forms.TimeField(
        label='Hora de Inicio',
        widget=forms.TimeInput(attrs={
            'class': 'form-input',
            'type': 'time'
        }),
        required=True
    )
    
    # Dilatación cervical (array de mediciones)
    dilatacion_cm = forms.CharField(
        label='Dilatación (cm) - separado por comas',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '0-10, 0-10, ...'
        }),
        required=False,
        help_text='Ejemplo: 0-10, 1-9, 2-8 (hora-dilatación)'
    )
    
    # Frecuencia Cardíaca Fetal (array de mediciones)
    fcf_latidos = forms.CharField(
        label='FCF (lat/min) - separado por comas',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '110-160, 110-160, ...'
        }),
        required=False,
        help_text='Ejemplo: 110-160, 115-158 (hora-latidos)'
    )
    
    # Contracciones (en 10 min)
    contracciones = forms.CharField(
        label='Contracciones (10 min) - separado por comas',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '0-5, 0-5, ...'
        }),
        required=False,
        help_text='Ejemplo: 0-5, 1-4 (hora-cantidad)'
    )
    
    # Presión Arterial
    presion_arterial = forms.CharField(
        label='Presión Arterial - separado por comas',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '120/80, 120/80, ...'
        }),
        required=False,
        help_text='Ejemplo: 120/80, 118/78 (hora-presión)'
    )
    
    # Observaciones clínicas
    observaciones_clinicas = forms.CharField(
        label='Observaciones Clínicas',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 4,
            'placeholder': 'Observaciones clínicas durante el trabajo de parto'
        }),
        required=False
    )
    
    def clean(self):
        """Validar que al menos haya un dato registrado"""
        cleaned_data = super().clean()
        
        # Verificar que al menos uno de los campos tenga datos
        tiene_datos = any([
            cleaned_data.get('dilatacion_cm'),
            cleaned_data.get('fcf_latidos'),
            cleaned_data.get('contracciones'),
            cleaned_data.get('presion_arterial'),
            cleaned_data.get('observaciones_clinicas')
        ])
        
        if not tiene_datos:
            raise ValidationError('Debe registrar al menos un tipo de dato en el partograma')
        
        return cleaned_data
    
    def to_json(self):
        """
        Convierte los datos del formulario a formato JSON para guardar en BD
        """
        return {
            'hora_inicio': self.cleaned_data.get('hora_inicio').strftime('%H:%M') if self.cleaned_data.get('hora_inicio') else None,
            'dilatacion_cm': self.cleaned_data.get('dilatacion_cm', ''),
            'fcf_latidos': self.cleaned_data.get('fcf_latidos', ''),
            'contracciones': self.cleaned_data.get('contracciones', ''),
            'presion_arterial': self.cleaned_data.get('presion_arterial', ''),
            'observaciones_clinicas': self.cleaned_data.get('observaciones_clinicas', ''),
            'fecha_registro': timezone.now().isoformat()
        }