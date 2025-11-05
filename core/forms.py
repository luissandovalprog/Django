"""
Formularios para la gestión de Madres, Partos y Recién Nacidos
"""

from django import forms
from .models import Madre, Parto, RecienNacido, DiagnosticoCIE10


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
