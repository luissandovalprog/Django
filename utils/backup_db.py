import os
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def backup_postgresql():
    """
    Genera un backup de la base de datos PostgreSQL.
    """
    # Configuración de la base de datos desde variables de entorno
    db_name = os.getenv('DB_NAME', 'hospital_obstetricia')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    # Ruta a pg_dump (opcional, por defecto intenta usar 'pg_dump' del PATH)
    pg_dump_path = os.getenv('PG_DUMP_PATH', 'pg_dump')

    # Directorio de backups
    backup_dir = Path(__file__).resolve().parent.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)

    # Nombre del archivo de backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f"postgres_backup_{timestamp}.dump"

    # Comando pg_dump
    # -F c: Formato custom (comprimido por defecto)
    # -b: Incluir large objects
    # -v: Verbose
    # -f: Archivo de salida
    command = [
        pg_dump_path,
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-F', 'c',
        '-b',
        '-v',
        '-f', str(backup_file),
        db_name
    ]

    # Configurar entorno para pasar la contraseña
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password

    print(f"Iniciando backup de PostgreSQL: {db_name}...")
    try:
        subprocess.run(command, env=env, check=True)
        print(f"Backup completado exitosamente: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al realizar el backup: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Ejecutable no encontrado en '{pg_dump_path}'. Asegúrate de que PostgreSQL esté instalado y configurado correctamente.")
        return False

if __name__ == "__main__":
    backup_postgresql()
