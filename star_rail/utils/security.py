import base64
import random
import string
import time

from Crypto.Cipher import AES

from star_rail import exceptions as error

__all__ = ["AES128"]


class AES128:
    def __init__(self, salt: str) -> None:
        self.salt = salt
        self.cipher = AES.new(AES128.pad_str_to_multiple_of_16(salt), AES.MODE_ECB)

    @staticmethod
    def pad_str_to_multiple_of_16(s: str):
        """对字符串补足为长度16的倍数"""
        while len(s) % 16 != 0:
            s += "\0"
        return str.encode(s)

    @staticmethod
    def generate_salt(length: int = 16):
        """根据时间生成随机 salt"""
        current_time = int(time.time())
        random.seed(current_time)
        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def encrypt(self, data: str):
        try:
            encrypt_data = self.cipher.encrypt(AES128.pad_str_to_multiple_of_16(data))
            encrypt_data = str(base64.encodebytes(encrypt_data), encoding="utf8").replace("\n", "")
        except Exception as e:
            raise error.EncryptError("Encrypt error, {}", e)
        return encrypt_data

    def decrypt(self, data: str):
        try:
            encrypted_raw = base64.decodebytes(bytes(data, encoding="utf8"))
            row_data = self.cipher.decrypt(encrypted_raw).rstrip(b"\0").decode("utf8")
        except Exception as e:
            raise error.DecryptError("Decrypt error, {}", e)
        return str(row_data)
