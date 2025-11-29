import os
import django
from django.conf import settings
from django.test import Client

def check_apps():
    """
    Verifica que las aplicaciones estén cargadas y respondan correctamente.
    """
    print("Configurando entorno Django...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    print("\nVerificando aplicaciones instaladas...")
    apps_to_check = ['accounts', 'core', 'reportes', 'auditoria', 'notifications']
    
    # Verificar registro de apps
    from django.apps import apps
    installed_apps = apps.get_app_configs()
    installed_app_names = [app.name for app in installed_apps]

    all_apps_loaded = True
    for app in apps_to_check:
        if app in installed_app_names:
            print(f"[OK] App '{app}' cargada correctamente.")
        else:
            print(f"[ERROR] App '{app}' NO encontrada en INSTALLED_APPS.")
            all_apps_loaded = False

    if not all_apps_loaded:
        print("\n[!] Deteniendo pruebas debido a aplicaciones faltantes.")
        return

    print("\nVerificando respuestas HTTP (Smoke Tests)...")
    client = Client()
    
    urls_to_test = {
        'accounts': '/accounts/login/',
        'core': '/sistema/dashboard/',
        'reportes': '/reportes/',
        'auditoria': '/auditoria/historial/',
        'notifications': '/notifications/api/conteo/',
    }

    for app, url in urls_to_test.items():
        try:
            # Usar 'localhost' como host para evitar error DisallowedHost
            response = client.get(url, follow=True, HTTP_HOST='localhost')
            if response.status_code in [200, 302]:
                print(f"[OK] {app.capitalize()} ({url}) responde con estado {response.status_code}.")
            elif response.status_code == 404:
                 print(f"[WARNING] {app.capitalize()} ({url}) no encontrada (404). Verifica la URL.")
            else:
                print(f"[ERROR] {app.capitalize()} ({url}) falló con estado {response.status_code}.")
        except Exception as e:
            print(f"[ERROR] Excepción al probar {app}: {e}")

    print("\nPruebas finalizadas.")

if __name__ == "__main__":
    # Asegurar que el directorio de logs exista para evitar errores de configuración
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        print(f"Creando directorio de logs faltante: {log_dir}")
        os.makedirs(log_dir)

    check_apps()
