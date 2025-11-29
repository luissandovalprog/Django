# Proyecto Integrado DJANGO - Hospital Clínico Herminda Martín
## Sistema de Trazabilidad e Información de Partos y Recién Nacidos

Este proyecto es una aplicación web desarrollada en Django para la gestión y trazabilidad de partos y recién nacidos.

## Manual de Usuario: Configuración e Instalación

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### 1. Requisitos Previos

Asegúrate de tener instalado lo siguiente en tu sistema:

*   **Python 3.12.10+**: [Descargar Python](https://www.python.org/downloads/)
*   **PostgreSQL 14+**: [Descargar PostgreSQL](https://www.postgresql.org/download/)

### 1. Instalación


2.  **Crear y activar un entorno virtual:**

    *   **Windows:**
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

### 2. Configuración de la Base de Datos

1.  **Crear la base de datos en PostgreSQL:**
    Abre pgAdmin o tu terminal de SQL y ejecuta:

    ```sql
    CREATE DATABASE django; 
    ```

2.  **Configurar variables de entorno:**
    Crea un archivo llamado `.env` en la raíz del proyecto (al mismo nivel que `manage.py`) y agrega la siguiente configuración (ajusta los valores según tu instalación de PostgreSQL):

    ```env
    DEBUG=True
    SECRET_KEY=tu_clave_secreta_segura
    ALLOWED_HOSTS=localhost,127.0.0.1

    # Configuración de Base de Datos
    DB_NAME=django
    DB_USER=postgres
    DB_PASSWORD=tu_contraseña
    DB_HOST=localhost
    DB_PORT=5432
    PG_DUMP_PATH=C:\Program Files\PostgreSQL\18\bin\pg_dump.exe

    ENCRYPTION_KEY=tu_clave_de_encriptado_aqui
    ```

        La clave de encriptado la puedes generar utilizando los siguientes comandos en la terminal:
            python manage.py shell
                (dentro de la shell)
                from cryptography.fernet import Fernet
                key = Fernet.generate_key()
                key
        copia y pega el output en ENCRYPTION_KEY, repite el proceso para SECRET_KEY


3.  **Aplicar migraciones:**
    Esto creará las tablas necesarias en la base de datos.

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4.  **Crear un superusuario (Administrador):**
    Para acceder al panel de administración de Django.

    ```bash
    python manage.py createsuperuser
    ```

### 3. Ejecución de la Aplicación

#### Servidor de Desarrollo (Para pruebas y desarrollo)
Este servidor se recarga automáticamente cuando haces cambios en el código.

```bash
python manage.py runserver
```
Accede a la aplicación en: `http://127.0.0.1:8000/`

#### Servidor de Producción (Waitress)
Para simular un entorno de producción en Windows.

```bash
waitress-serve --listen=*:8000 --threads=10 config.wsgi:application
```

### 4 Gestión de Usuarios y Roles

Una vez que la aplicación esté corriendo y hayas creado el superusuario:

1.  **Iniciar Sesión:**
    Ingresa a `http://127.0.0.1:8000/accounts/login/` con las credenciales del superusuario que creaste anteriormente.

2.  **Acceder a Gestión de Usuarios:**
    En el menú principal o barra de navegación, busca la opción **"Gestión de Usuarios"**.

3.  **Crear Roles:**
    *   Dentro de la gestión, ve a la pestaña o sección de **Roles**.
    *   Haz clic en **"Crear Rol"**.
    *   Define el nombre del rol (ej. "Matrona", "Médico", "Administrativo") y selecciona los permisos correspondientes según las funciones que deba realizar.
    *   Guarda el rol.

4.  **Crear Usuarios:**
    *   Vuelve a la lista de usuarios.
    *   Haz clic en **"Crear Usuario"**.
    *   Completa los datos personales (RUT, Nombre, Email) y las credenciales.
    *   **Importante:** En el campo de **Rol**, selecciona el rol que creaste previamente.
    *   Guarda el usuario.

### 5. Archivos Estáticos

Si ves que la página no carga los estilos correctamente, asegúrate de recolectar los archivos estáticos y volver a correr el servidor:

```bash
python manage.py collectstatic
```

### 6. Pruebas finales
    Ejecuta en la terminal (con Venv activado) python manage.py test
    para validar que la instalacion es correcta y segura. Deberías ver el resultado OK
    indicando que el núcleo clínico y los reportes funcionan correctamente.

# En caso de no existir las carpetas "logs" y "backups" en el directorio raiz, porfavor crearlas
# de lo contrario el software no arrancará