"""
Formularios para la gestión de Madres, Partos y Recién Nacidos
"""
import uuid
from django.db import models
from django import forms
from .models import Madre, Parto, RecienNacido, DiagnosticoCIE10, Correccion, Indicacion
from django.forms import inlineformset_factory

class PartoForm(forms.ModelForm):
    class Meta:
        model = Parto
        fields = ['madre', 'fecha_parto', 'edad_gestacional', 'tipo_parto', 'anestesia']
        widgets = {
            'madre': forms.Select(attrs={'class': 'select'}),
            'fecha_parto': forms.DateTimeInput(attrs={'class': 'input', 'type': 'datetime-local'}),
            'edad_gestacional': forms.NumberInput(attrs={'class': 'input', 'min': '20', 'max': '45'}),
            'tipo_parto': forms.Select(attrs={'class': 'select'}),
            'anestesia': forms.Select(attrs={'class': 'select'}),
        }

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
            'placeholder': 'Nombre completo de la madre'
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
            'ficha_clinica_id',
            'fecha_nacimiento',
            'nacionalidad',
            'pertenece_pueblo_originario',
            'prevision',
            'antecedentes_medicos'
        ]
        widgets = {
            'ficha_clinica_id': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control'}),
            'pertenece_pueblo_originario': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prevision': forms.Select(attrs={'class': 'form-control'}),
            'antecedentes_medicos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'ficha_clinica_id': 'Ficha Clínica',
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


class PartoForm(forms.ModelForm):
    """
    Formulario para crear/editar Parto
    """
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
                'max': '45'
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
            choices = [(None, '---------')]
            for madre in Madre.objects.all():
                nombre = madre.get_nombre()
                ficha = madre.ficha_clinica_id
                label = f"{nombre} - Ficha: {ficha}" if nombre and ficha else (nombre or ficha or str(madre.id))
                choices.append((madre.id, label))
            self.fields['madre'].choices = choices
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.usuario_registro = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class RecienNacidoForm(forms.ModelForm):
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'rut_provisorio', 'estado_al_nacer', 'sexo', 
            'peso_gramos', 'talla_cm', 'apgar_1_min', 'apgar_5_min',
            'profilaxis_vit_k', 'profilaxis_oftalmica'
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'select'}),
            'rut_provisorio': forms.TextInput(attrs={'class': 'input'}),
            'estado_al_nacer': forms.Select(attrs={'class': 'select'}),
            'sexo': forms.Select(attrs={'class': 'select'}),
            'peso_gramos': forms.NumberInput(attrs={'class': 'input', 'min': '500', 'max': '6000'}),
            'talla_cm': forms.NumberInput(attrs={'class': 'input', 'min': '25', 'max': '65', 'step': '0.1'}),
            'apgar_1_min': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '10'}),
            'apgar_5_min': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '10'}),
            'profilaxis_vit_k': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
            'profilaxis_oftalmica': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
        }

class RecienNacidoForm(forms.ModelForm):
    """
    Formulario para crear/editar Recién Nacido
    """
    class Meta:
        model = RecienNacido
        fields = [
            'parto',
            'rut_provisorio',
            'estado_al_nacer',
            'sexo',
            'peso_gramos',
            'talla_cm',
            'apgar_1_min',
            'apgar_5_min',
            'profilaxis_vit_k',
            'profilaxis_oftalmica',
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'form-control'}),
            'rut_provisorio': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_al_nacer': forms.Select(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'peso_gramos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '500',
                'max': '6000'
            }),
            'talla_cm': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '25',
                'max': '65',
                'step': '0.1'
            }),
            'apgar_1_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
            'apgar_5_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
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
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.usuario_registro = self.user
        if commit:
            instance.save()
        return instance

class CorreccionForm(forms.ModelForm):
    class Meta:
        model = Correccion
        fields = ['campo_corregido', 'valor_original', 'valor_nuevo', 'justificacion']
        widgets = {
            'campo_corregido': forms.Select(attrs={'class': 'select'}),
            'valor_original': forms.TextInput(attrs={'class': 'input bg-gray-100', 'readonly': True}),
            'valor_nuevo': forms.TextInput(attrs={'class': 'input border-green-500 border-2'}),
            'justificacion': forms.Textarea(attrs={'class': 'textarea border-green-500 border-2', 'rows': 4, 'placeholder': 'Describa detalladamente el motivo... (mínimo 20 caracteres)'}),
        }
        labels = {
            'campo_corregido': 'Campo a Corregir',
            'valor_original': 'Valor Original (No se modificará)',
            'valor_nuevo': 'Valor Corregido',
            'justificacion': 'Justificación de la Corrección',
        }

    def clean_justificacion(self):
        justificacion = self.cleaned_data.get('justificacion')
        if len(justificacion) < 20:
            raise forms.ValidationError('La justificación debe tener al menos 20 caracteres.')
        return justificacion

class EpicrisisForm(forms.ModelForm):
    # Campos de Epicrisis que no son modelo, se guardarán en JSONField
    motivo_ingreso = forms.CharField(label="Motivo de Ingreso", widget=forms.TextInput(attrs={'class': 'input'}), required=False)
    resumen_evolucion = forms.CharField(label="Resumen de Evolución *", widget=forms.Textarea(attrs={'class': 'textarea', 'rows': 4}))
    diagnostico_egreso = forms.CharField(label="Diagnóstico de Egreso *", widget=forms.Textarea(attrs={'class': 'textarea', 'rows': 3}))
    condicion_egreso = forms.ChoiceField(
        label="Condición al Egreso", 
        choices=[('buena', 'Buena'), ('regular', 'Regular'), ('grave', 'Grave'), ('fallecido', 'Fallecido')],
        widget=forms.Select(attrs={'class': 'select'})
    )
    control_posterior = forms.CharField(label="Control Posterior", widget=forms.TextInput(attrs={'class': 'input'}), required=False)
    indicaciones_alta = forms.CharField(label="Indicaciones al Alta", widget=forms.Textarea(attrs={'class': 'textarea', 'rows': 3}), required=False)
    observaciones = forms.CharField(label="Observaciones", widget=forms.Textarea(attrs={'class': 'textarea', 'rows': 2}), required=False)

    class Meta:
        model = Parto
        fields = []

class IndicacionForm(forms.ModelForm):
    class Meta:
        model = Indicacion
        fields = ['tipo', 'descripcion', 'dosis', 'via', 'frecuencia']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'select'}),
            'descripcion': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Paracetamol'}),
            'dosis': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: 500mg'}),
            'via': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Oral'}),
            'frecuencia': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Cada 8 horas'}),
        }
        labels = {
            'descripcion': 'Descripción *',
        }

# Creamos el Formset
IndicacionFormSet = inlineformset_factory(
    Parto, 
    Indicacion, 
    form=IndicacionForm, 
    extra=1, 
    can_delete=True,
    fk_name='parto'
)