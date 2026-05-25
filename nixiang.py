import hmac
import hashlib
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# ===================== 固定配置（和JS代码一致）=====================
HMAC_FIXED_KEY = b"new-api-captcha-aes-v1"
AES_BLOCK_SIZE = 128  # PKCS7 这里单位是 bit，不是 byte


def captcha_encrypt(captcha_key: str, plain_text: str) -> str:
    """
    生成验证码的 data 参数
    :param captcha_key: 后端返回的验证码 key，例如: 1779004862798bc2ae
    :param plain_text: 坐标字符串，例如: 155,192;252,111
    :return: 最终的 data 字符串
    """
    HMAC_FIXED_KEY = b"new-api-captcha-aes-v1"
    AES_BLOCK_SIZE = 128  # PKCS7 这里单位是 bit，不是 byte
    # 1. 生成 AES-256 密钥（HMAC-SHA256）
    aes_key = hmac.new(
        key=HMAC_FIXED_KEY,
        msg=captcha_key.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()  # 32字节

    # 2. 生成 16 字节随机 IV
    iv = os.urandom(16)
    # 3. PKCS7 填充
    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()

    # 4. AES-256-CBC 加密
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # 5. 拼接 IV + 密文，再 Base64
    result_bytes = iv + ciphertext
    final_data = base64.b64encode(result_bytes).decode("utf-8")

    return final_data


if __name__ == "__main__":
    CAPTCHA_KEY = "1779007964b6a0c6e9"
    POINTS = "28,41;75,164"

    data = captcha_encrypt(CAPTCHA_KEY, POINTS)
    print("✅ 最终上传用的 data 参数：")
    print(data)
    if data=='Q9ThrvCYQ05kJIxFw81u9dY6TMcMpoUUo3Nm8pDjmSw=':
        print("验证码正确")