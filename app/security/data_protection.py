from cryptography.fernet import Fernet
import os

class DataProtection:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher_suite = Fernet(self.key)

    def encrypt_data(self, data):
        """データの暗号化"""
        return self.cipher_suite.encrypt(str(data).encode())

    def decrypt_data(self, encrypted_data):
        """データの復号化"""
        return self.cipher_suite.decrypt(encrypted_data).decode() 