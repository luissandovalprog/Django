"""
Utilidades de cifrado para datos sensibles
Usa cryptography para cifrado AES simétrico
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as PBKDF2
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import base64
import hashlib


class CryptoService:
    """
    Servicio de cifrado/descifrado para datos sensibles
    """
    
    def __init__(self):
        # Generar clave de cifrado desde la configuración
        self.encryption_key = self._get_fernet_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_fernet_key(self):
        """
        Obtiene o genera una clave Fernet válida
        """
        if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
            # Crear hash de la clave de configuración para asegurar 32 bytes
            key_hash = hashlib.sha256(settings.ENCRYPTION_KEY).digest()
            return base64.urlsafe_b64encode(key_hash)
        else:
            # Generar clave temporal para desarrollo (NO usar en producción)
            return Fernet.generate_key()
    
    def encrypt(self, plain_text):
        """
        Cifra texto plano
        
        Args:
            plain_text (str): Texto a cifrar
            
        Returns:
            str: Texto cifrado en base64
        """
        if not plain_text:
            return None
        
        encrypted_data = self.fernet.encrypt(plain_text.encode())
        return encrypted_data.decode()
    
    def decrypt(self, encrypted_text):
        """
        Descifra texto cifrado
        
        Args:
            encrypted_text (str): Texto cifrado en base64
            
        Returns:
            str: Texto plano descifrado
        """
        if not encrypted_text:
            return None
        
        try:
            decrypted_data = self.fernet.decrypt(encrypted_text.encode())
            return decrypted_data.decode()
        except Exception as e:
            # En caso de error de descifrado, retornar None
            return None
    
    def hash_data(self, data):
        """
        Genera un hash SHA-256 de los datos (para búsquedas)
        
        Args:
            data (str): Datos a hashear
            
        Returns:
            str: Hash hexadecimal
        """
        if not data:
            return None
        
        return hashlib.sha256(data.encode()).hexdigest()


# Instancia global del servicio de cifrado
crypto_service = CryptoService()
