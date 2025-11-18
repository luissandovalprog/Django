# accounts/forms.py
"""
Formularios para gestión de usuarios
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import Usuario, Rol
import re


class CustomUsuarioCreationForm(UserCreationForm):
    """Formulario para crear nuevo usuario"""
    
    nombre_completo = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nombre completo del usuario'
        }),
        label='Nombre Completo'
    )
    
    rut = forms.CharField(
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '12.345.678-9'
        }),
        label='RUT'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'usuario@hospital.cl'
        }),
        label='Email'
    )
    
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'nombre.usuario'
        }),
        label='Usuario (Login)'
    )
    
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Rol',
        empty_label='Seleccione un rol...'
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••'
        }),
        help_text='Mínimo 8 caracteres'
    )
    
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••'
        })
    )
    
    activo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Usuario Activo'
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre_completo', 'rut', 'rol', 'password1', 'password2', 'activo')

    def clean_rut(self):
        """Valida el formato del RUT chileno"""
        rut = self.cleaned_data.get('rut', '')
        
        # Limpiar el RUT
        rut_limpio = re.sub(r'[.-]', '', rut).upper()
        
        if len(rut_limpio) < 8:
            raise ValidationError('El RUT debe tener al menos 8 caracteres')
        
        # Verificar que el RUT no esté duplicado
        if Usuario.objects.filter(rut=rut).exists():
            raise ValidationError('Este RUT ya está registrado')
        
        return rut

    def clean_email(self):
        """Valida que el email no esté duplicado"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado')
        return email

    def clean_username(self):
        """Valida que el username no esté duplicado"""
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso')
        return username

    def clean_password2(self):
        """Valida que las contraseñas coincidan"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden')
        
        return password2


class CustomUsuarioChangeForm(forms.ModelForm):
    """Formulario para editar usuario existente"""
    
    nombre_completo = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nombre completo del usuario'
        }),
        label='Nombre Completo'
    )
    
    rut = forms.CharField(
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '12.345.678-9'
        }),
        label='RUT'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'usuario@hospital.cl'
        }),
        label='Email'
    )
    
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'nombre.usuario'
        }),
        label='Usuario (Login)'
    )
    
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Rol',
        empty_label='Seleccione un rol...'
    )
    
    activo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Usuario Activo'
    )
    
    is_staff = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Acceso al Admin de Django'
    )
    
    # Campos opcionales para cambiar contraseña
    nueva_password = forms.CharField(
        label='Nueva Contraseña (opcional)',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Dejar en blanco para mantener actual'
        }),
        help_text='Deje en blanco si no desea cambiar la contraseña'
    )
    
    confirmar_password = forms.CharField(
        label='Confirmar Nueva Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirme la nueva contraseña'
        })
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre_completo', 'rut', 'rol', 'activo', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El username no puede ser modificado después de creado
        if self.instance and self.instance.pk:
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].help_text = 'El nombre de usuario no puede ser modificado'

    def clean_rut(self):
        """Valida el formato del RUT chileno"""
        rut = self.cleaned_data.get('rut', '')
        
        # Limpiar el RUT
        rut_limpio = re.sub(r'[.-]', '', rut).upper()
        
        if len(rut_limpio) < 8:
            raise ValidationError('El RUT debe tener al menos 8 caracteres')
        
        # Verificar que el RUT no esté duplicado (excepto el actual)
        if self.instance and self.instance.pk:
            if Usuario.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este RUT ya está registrado')
        else:
            if Usuario.objects.filter(rut=rut).exists():
                raise ValidationError('Este RUT ya está registrado')
        
        return rut

    def clean_email(self):
        """Valida que el email no esté duplicado"""
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk:
            if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este email ya está registrado')
        else:
            if Usuario.objects.filter(email=email).exists():
                raise ValidationError('Este email ya está registrado')
        return email

    def clean(self):
        """Valida que las contraseñas coincidan si se están cambiando"""
        cleaned_data = super().clean()
        nueva_password = cleaned_data.get('nueva_password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        if nueva_password or confirmar_password:
            if nueva_password != confirmar_password:
                raise ValidationError({
                    'confirmar_password': 'Las contraseñas no coinciden'
                })
            
            if nueva_password and len(nueva_password) < 8:
                raise ValidationError({
                    'nueva_password': 'La contraseña debe tener al menos 8 caracteres'
                })
        
        return cleaned_data

    def save(self, commit=True):
        """Guarda el usuario y actualiza la contraseña si se proporcionó una nueva"""
        user = super().save(commit=False)
        
        nueva_password = self.cleaned_data.get('nueva_password')
        if nueva_password:
            user.set_password(nueva_password)
        
        if commit:
            user.save()
        
        return user

class RolForm(forms.ModelForm):
    """
    Formulario para crear/editar Roles con permisos RBAC granulares
    """
    
    class Meta:
        model = Rol
        fields = [
            'nombre',
            'descripcion',
            # Permisos de Admisiones
            'puede_crear_admision_madre',
            'puede_editar_admision_madre',
            # Permisos de Dashboard
            'puede_ver_lista_administrativa_madres',
            'puede_ver_dashboard_clinico',
            # Permisos de Partos
            'puede_crear_parto',
            'puede_editar_parto',
            'puede_ver_todos_partos',
            # Permisos de Partogramas y Epicrisis
            'puede_crear_editar_partograma',
            'puede_crear_editar_epicrisis',
            # Permisos de Reportes y Gestión
            'puede_generar_reportes_rem',
            'puede_ver_auditoria',
            'puede_gestionar_usuarios',
            'puede_eliminar_registros',
            'puede_anexar_correccion',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Matrona Clínica'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Descripción del rol y sus responsabilidades'
            }),
        }
        labels = {
            'nombre': 'Nombre del Rol',
            'descripcion': 'Descripción',
            # Admisiones
            'puede_crear_admision_madre': 'Crear Admisiones de Madres',
            'puede_editar_admision_madre': 'Editar Admisiones de Madres',
            # Dashboard
            'puede_ver_lista_administrativa_madres': 'Ver Lista Administrativa (solo datos demográficos)',
            'puede_ver_dashboard_clinico': 'Ver Dashboard Clínico',
            # Partos
            'puede_crear_parto': 'Crear Registros de Parto',
            'puede_editar_parto': 'Editar Registros de Parto',
            'puede_ver_todos_partos': 'Ver Todos los Partos (sin restricción de turno)',
            # Partogramas y Epicrisis
            'puede_crear_editar_partograma': 'Crear/Editar Partogramas',
            'puede_crear_editar_epicrisis': 'Crear/Editar Epicrisis',
            # Reportes y Gestión
            'puede_generar_reportes_rem': 'Generar Reportes REM',
            'puede_ver_auditoria': 'Acceder a Auditoría',
            'puede_gestionar_usuarios': 'Gestionar Usuarios',
            'puede_eliminar_registros': 'Eliminar Registros',
            'puede_anexar_correccion': 'Anexar Correcciones',
        }
    
    def clean_nombre(self):
        """Validar que el nombre del rol no esté duplicado"""
        nombre = self.cleaned_data.get('nombre')
        
        # Excluir el rol actual en caso de edición
        if self.instance and self.instance.pk:
            if Rol.objects.filter(nombre=nombre).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Ya existe un rol con este nombre')
        else:
            if Rol.objects.filter(nombre=nombre).exists():
                raise ValidationError('Ya existe un rol con este nombre')
        
        return nombre
    
    def clean(self):
        """Validaciones cruzadas de permisos"""
        cleaned_data = super().clean()
        
        # Validación 1: Si puede editar parto, debe poder crear parto
        if cleaned_data.get('puede_editar_parto') and not cleaned_data.get('puede_crear_parto'):
            raise ValidationError({
                'puede_editar_parto': 'Para editar partos, primero debe poder crearlos'
            })
        
        # Validación 2: Admin Sistema no debe tener acceso clínico
        nombre = cleaned_data.get('nombre', '')
        if 'admin sistema' in nombre.lower():
            if cleaned_data.get('puede_ver_dashboard_clinico') or cleaned_data.get('puede_ver_lista_administrativa_madres'):
                raise ValidationError(
                    'El rol "Admin Sistema" NO debe tener acceso a datos de pacientes (principio de segmentación)'
                )
        
        # Validación 3: Administrativo no debe ver dashboard clínico
        if 'administrativo' in nombre.lower():
            if cleaned_data.get('puede_ver_dashboard_clinico'):
                raise ValidationError({
                    'puede_ver_dashboard_clinico': 'El rol Administrativo NO debe ver datos clínicos'
                })
        
        return cleaned_data