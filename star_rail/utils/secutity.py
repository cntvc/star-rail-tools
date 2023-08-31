import base64
import random
import string
import time

from Crypto.Cipher import AES

__all__ = ["AES128", "AES_PREFIX"]


AES_PREFIX = "aes128_"


class AES128:
    def __init__(self, salt: str, prefix: str = AES_PREFIX) -> None:
        self.salt = salt
        self.cipher = AES.new(AES128.pad_str_to_multiple_of_16(salt), AES.MODE_ECB)
        self.prefix = prefix

    @staticmethod
    def pad_str_to_multiple_of_16(s: str):
        """对字符串补位为长度16的倍数"""
        while len(s) % 16 != 0:
            s += "\0"
        return str.encode(s)

    @staticmethod
    def generate_salt(length: int = 16):
        """根据时间生成随机 salt"""
        current_time = int(time.time())
        random.seed(current_time)
        salt = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
        return salt

    def encrypt(self, data: str):
        encrypt_data = self.cipher.encrypt(AES128.pad_str_to_multiple_of_16(data))
        return self.prefix + str(base64.encodebytes(encrypt_data), encoding="utf8").replace(
            "\n", ""
        )

    def decrypt(self, data: str):
        if data.startswith(self.prefix):
            data = data[len(self.prefix) :]  # noqa
        encrypted_raw = base64.decodebytes(bytes(data, encoding="utf8"))
        row_data = self.cipher.decrypt(encrypted_raw).rstrip(b"\0").decode("utf8")
        return str(row_data)
