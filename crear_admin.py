import os
import django

# Configurar entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Datos del superusuario (Cámbialos si quieres)
USERNAME = "Supervisor"
PASSWORD = "supervisor"  # ¡Cámbiala después!
EMAIL = "supervisor@hospital.com"
RUT = "11.111.111-1"
NOMBRE = "Supervisor"

if not User.objects.filter(username=USERNAME).exists():
    print("Creando superusuario...")
    User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
        rut=RUT,
        nombre_completo=NOMBRE
    )
    print("¡Superusuario creado con éxito!")
else:
    print("El superusuario ya existe. No se hizo nada.")