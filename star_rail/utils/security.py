import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

__all__ = ["AES128"]


class AES128:
    def __init__(self, key: str) -> None:
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    @staticmethod
    def generate_aes_key():
        key = get_random_bytes(16)
        return base64.b64encode(key).decode("UTF-8")

    def encrypt(self, plaintext):
        ciphertext = self.cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
        encrypted_base64 = base64.b64encode(ciphertext)
        return encrypted_base64

    def decrypt(self, encrypted_base64):
        ciphertext = base64.b64decode(encrypted_base64)
        decrypted_text = unpad(self.cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_text.decode("utf-8")
