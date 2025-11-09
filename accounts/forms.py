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