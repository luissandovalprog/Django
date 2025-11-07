# En accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, Rol

class CustomUsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'nombre_completo', 'rut', 'email', 'rol', 'activo')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'input'}),
            'rut': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'rol': forms.Select(attrs={'class': 'select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
        }

class CustomUsuarioChangeForm(UserChangeForm):
    password = None # No manejar password en el formulario de edición
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = ('username', 'nombre_completo', 'rut', 'email', 'rol', 'activo', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'input'}),
            'rut': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'rol': forms.Select(attrs={'class': 'select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
        }