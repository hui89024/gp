from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """AES加密服务，用于券商账户密码加密"""

    def __init__(self):
        key = settings.ENCRYPTION_KEY
        if not key:
            key = Fernet.generate_key().decode()
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        """加密明文"""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密密文"""
        return self._fernet.decrypt(ciphertext.encode()).decode()


encryption_service = EncryptionService()
