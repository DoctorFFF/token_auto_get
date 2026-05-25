import hmac
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


# 固定字节串：按你的加密流程风格保留为 HMAC 输入 key
FIXED_HMAC_KEY = b"new-api-captcha-aes-v1"

# AES block size，单位是 bit
AES_BLOCK_SIZE = 128


def derive_aes_key(context_key: str) -> bytes:
    """
    用 HMAC-SHA256 派生 AES-256 密钥
    """
    return hmac.new(
        key=FIXED_HMAC_KEY,
        msg=context_key.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()


def decrypt_iv_cipher_base64(context_key: str, data_b64: str) -> str:
    """
    解密 Base64(IV + ciphertext)

    :param context_key: 用于派生 AES key 的上下文字符串
    :param data_b64: Base64 编码后的 IV + 密文
    :return: 解密后的 UTF-8 字符串
    """
    aes_key = derive_aes_key(context_key)

    raw = base64.b64decode(data_b64)

    if len(raw) < 16:
        raise ValueError("数据长度不足，无法拆分 IV")

    iv = raw[:16]
    ciphertext = raw[16:]

    if len(ciphertext) == 0:
        raise ValueError("没有密文内容")

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    plain_bytes = unpadder.update(padded_plain) + unpadder.finalize()

    return plain_bytes.decode("utf-8")


if __name__ == "__main__":
    # 这里填你自己的测试上下文 key
    CONTEXT_KEY = "1779603213242a2688"

    # 这里填 Base64(IV + ciphertext)
    DATA_B64 = "Tc3NcXda5m9jAHLpOPfdG8hAl1WxigSPGDhq+0BIyYKGIEvTVc6UUTEhLjiJAQs2"

    try:
        plain_text = decrypt_iv_cipher_base64(CONTEXT_KEY, DATA_B64)
        print("解密成功：")
        print(plain_text)
    except Exception as e:
        print("解密失败：", repr(e))