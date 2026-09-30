import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


AES_KEY_SIZE = 32
NONCE_SIZE = 12


class CryptoError(Exception):
    """Base exception for messaging cryptographic operations."""


class InvalidKeyError(CryptoError):
    """Raised when an encryption key is invalid."""


class DecryptionError(CryptoError):
    """Raised when encrypted data cannot be decrypted."""


@dataclass(frozen=True)
class EncryptedData:
    """
    Container for AES-GCM encrypted data.

    nonce:
        Random nonce used during encryption.

    ciphertext:
        Encrypted payload including the GCM authentication tag.
    """

    nonce: bytes
    ciphertext: bytes

    @property
    def nonce_base64(self) -> str:
        return base64.b64encode(self.nonce).decode("ascii")

    @property
    def ciphertext_base64(self) -> str:
        return base64.b64encode(self.ciphertext).decode("ascii")


def generate_key() -> bytes:
    """
    Generate a new 256-bit AES key.

    Returns:
        32 random bytes.
    """
    return AESGCM.generate_key(bit_length=256)


def validate_key(key: bytes) -> None:
    """
    Validate AES-256 key length.

    Raises:
        InvalidKeyError: if the key is not exactly 32 bytes.
    """
    if not isinstance(key, bytes):
        raise InvalidKeyError("Encryption key must be bytes.")

    if len(key) != AES_KEY_SIZE:
        raise InvalidKeyError(
            "AES-256 key must contain exactly 32 bytes."
        )


def encrypt(
    plaintext: bytes,
    key: bytes,
    *,
    associated_data: bytes | None = None,
) -> EncryptedData:
    """
    Encrypt plaintext using AES-256-GCM.

    Args:
        plaintext: Data to encrypt.
        key: 32-byte AES-256 key.
        associated_data: Optional authenticated but unencrypted data.

    Returns:
        EncryptedData containing nonce and ciphertext.
    """
    validate_key(key)

    if not isinstance(plaintext, bytes):
        raise TypeError("Plaintext must be bytes.")

    nonce = os.urandom(NONCE_SIZE)

    aesgcm = AESGCM(key)

    ciphertext = aesgcm.encrypt(
        nonce,
        plaintext,
        associated_data,
    )

    return EncryptedData(
        nonce=nonce,
        ciphertext=ciphertext,
    )


def decrypt(
    encrypted_data: EncryptedData,
    key: bytes,
    *,
    associated_data: bytes | None = None,
) -> bytes:
    """
    Decrypt AES-256-GCM encrypted data.

    Raises:
        InvalidKeyError: if the key is invalid.
        DecryptionError: if authentication/decryption fails.
    """
    validate_key(key)

    if not isinstance(encrypted_data, EncryptedData):
        raise TypeError(
            "encrypted_data must be an EncryptedData instance."
        )

    aesgcm = AESGCM(key)

    try:
        return aesgcm.decrypt(
            encrypted_data.nonce,
            encrypted_data.ciphertext,
            associated_data,
        )
    except Exception as exc:
        raise DecryptionError(
            "Unable to decrypt or authenticate encrypted data."
        ) from exc