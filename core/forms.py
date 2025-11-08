"""
Formularios CORREGIDOS
CAMBIO CRÍTICO: Agregado campo 'direccion' a MadreForm
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Madre, Parto, RecienNacido, DiagnosticoCIE10, Correccion, Indicacion
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError


class MadreForm(forms.ModelForm):
    """
    Formulario para crear/editar Madre
    CORREGIDO: Agregado campo 'direccion' separado de ficha_clinica_id
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
            'ficha_clinica_numero',  # AHORA es para el ID de ficha
            'direccion',         # NUEVO: Campo para dirección
            'fecha_nacimiento',
            'nacionalidad',
            'pertenece_pueblo_originario',
            'prevision',
            'antecedentes_medicos'
        ]
        widgets = {
            'ficha_clinica_numero': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: FC-2025-001'
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
        super().__init__(*args, **kwargs)
    
    def clean_rut(self):
        """Validar formato de RUT chileno"""
        rut = self.cleaned_data.get('rut', '')
        # Puedes agregar validación de RUT aquí
        return rut
    
    def clean_fecha_nacimiento(self):
        """Validar que la fecha de nacimiento sea válida"""
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            from datetime import date
            if fecha > date.today():
                raise ValidationError('La fecha de nacimiento no puede ser futura')
            # Calcular edad
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
    """Formulario para crear/editar Recién Nacido (sin cambios)"""
    
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'rut_provisorio', 'estado_al_nacer', 'sexo', 
            'peso_gramos', 'talla_cm', 'apgar_1_min', 'apgar_5_min',
            'profilaxis_vit_k', 'profilaxis_oftalmica'
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'form-control'}),
            'rut_provisorio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT provisorio'}),
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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
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
        if self.user and not instance.usuario_registro:
            instance.usuario_registro = self.user
        if commit:
            instance.save()
        return instance


class CorreccionForm(forms.ModelForm):
    """Formulario para anexar correcciones (sin cambios)"""
    
    class Meta:
        model = Correccion
        fields = ['campo_corregido', 'valor_original', 'valor_nuevo', 'justificacion']
        widgets = {
            'campo_corregido': forms.Select(attrs={'class': 'form-control'}),
            'valor_original': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'valor_nuevo': forms.TextInput(attrs={'class': 'form-control'}),
            'justificacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'campo_corregido': 'Campo a Corregir',
            'valor_original': 'Valor Original',
            'valor_nuevo': 'Valor Corregido',
            'justificacion': 'Justificación',
        }

    def clean_justificacion(self):
        justificacion = self.cleaned_data.get('justificacion', '')
        if len(justificacion) < 20:
            raise ValidationError('La justificación debe tener al menos 20 caracteres.')
        return justificacion


class EpicrisisForm(forms.Form):
    """Formulario para epicrisis (sin cambios)"""
    
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
    """Formulario para indicaciones médicas (sin cambios)"""
    
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