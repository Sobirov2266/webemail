import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


AES_KEY_SIZE = 32
NONCE_SIZE = 12
SALT_SIZE = 32

KEY_WRAP_INFO = b"webemail/message-key-wrap/v1"


class EnvelopeError(Exception):
    """Base exception for encrypted message envelope operations."""


class InvalidKeyMaterialError(EnvelopeError):
    """Raised when X25519 key material is invalid."""


class EnvelopeDecryptionError(EnvelopeError):
    """Raised when an encrypted envelope cannot be decrypted."""


@dataclass(frozen=True)
class EncryptedEnvelope:
    ciphertext: bytes
    nonce: bytes
    ephemeral_public_key: bytes
    salt: bytes
    wrapped_key: bytes
    wrap_nonce: bytes


def _validate_raw_key(
    value: bytes,
    expected_size: int,
    name: str,
) -> None:
    if not isinstance(value, bytes):
        raise InvalidKeyMaterialError(
            f"{name} must be bytes."
        )

    if len(value) != expected_size:
        raise InvalidKeyMaterialError(
            f"{name} must contain exactly "
            f"{expected_size} bytes."
        )


def _derive_key_encryption_key(
    shared_secret: bytes,
    salt: bytes,
) -> bytes:
    _validate_raw_key(
        shared_secret,
        32,
        "Shared secret",
    )

    _validate_raw_key(
        salt,
        SALT_SIZE,
        "Salt",
    )

    return HKDF(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        info=KEY_WRAP_INFO,
    ).derive(shared_secret)


def encrypt_for_recipient(
    plaintext: bytes,
    recipient_public_key: bytes,
    *,
    associated_data: bytes | None = None,
) -> EncryptedEnvelope:
    if not isinstance(plaintext, bytes):
        raise TypeError("Plaintext must be bytes.")

    _validate_raw_key(
        recipient_public_key,
        32,
        "Recipient public key",
    )

    try:
        recipient_key = (
            x25519.X25519PublicKey.from_public_bytes(
                recipient_public_key
            )
        )
    except ValueError as exc:
        raise InvalidKeyMaterialError(
            "Recipient public key is invalid."
        ) from exc

    # Ephemeral X25519 keypair.
    ephemeral_private_key = (
        x25519.X25519PrivateKey.generate()
    )

    ephemeral_public_key = (
        ephemeral_private_key
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )

    # ECDH.
    shared_secret = (
        ephemeral_private_key.exchange(
            recipient_key
        )
    )

    # Derive KEK from the shared secret.
    salt = os.urandom(SALT_SIZE)

    kek = _derive_key_encryption_key(
        shared_secret,
        salt,
    )

    # Random per-message DEK.
    dek = AESGCM.generate_key(
        bit_length=256
    )

    # Encrypt actual message.
    nonce = os.urandom(NONCE_SIZE)

    ciphertext = AESGCM(dek).encrypt(
        nonce,
        plaintext,
        associated_data,
    )

    # Encrypt/wrap DEK using KEK.
    wrap_nonce = os.urandom(NONCE_SIZE)

    wrapped_key = AESGCM(kek).encrypt(
        wrap_nonce,
        dek,
        associated_data,
    )

    return EncryptedEnvelope(
        ciphertext=ciphertext,
        nonce=nonce,
        ephemeral_public_key=ephemeral_public_key,
        salt=salt,
        wrapped_key=wrapped_key,
        wrap_nonce=wrap_nonce,
    )


def decrypt_for_recipient(
    envelope: EncryptedEnvelope,
    recipient_private_key: bytes,
    *,
    associated_data: bytes | None = None,
) -> bytes:
    if not isinstance(
        envelope,
        EncryptedEnvelope,
    ):
        raise TypeError(
            "envelope must be an "
            "EncryptedEnvelope instance."
        )

    _validate_raw_key(
        recipient_private_key,
        32,
        "Recipient private key",
    )

    _validate_raw_key(
        envelope.ephemeral_public_key,
        32,
        "Ephemeral public key",
    )

    _validate_raw_key(
        envelope.salt,
        SALT_SIZE,
        "Salt",
    )

    _validate_raw_key(
        envelope.nonce,
        NONCE_SIZE,
        "Nonce",
    )

    _validate_raw_key(
        envelope.wrap_nonce,
        NONCE_SIZE,
        "Wrap nonce",
    )

    try:
        private_key = (
            x25519.X25519PrivateKey
            .from_private_bytes(
                recipient_private_key
            )
        )

        ephemeral_public_key = (
            x25519.X25519PublicKey
            .from_public_bytes(
                envelope.ephemeral_public_key
            )
        )

        shared_secret = (
            private_key.exchange(
                ephemeral_public_key
            )
        )

        kek = _derive_key_encryption_key(
            shared_secret,
            envelope.salt,
        )

        # Recover DEK.
        dek = AESGCM(kek).decrypt(
            envelope.wrap_nonce,
            envelope.wrapped_key,
            associated_data,
        )

        _validate_raw_key(
            dek,
            AES_KEY_SIZE,
            "Data encryption key",
        )

        # Decrypt message.
        return AESGCM(dek).decrypt(
            envelope.nonce,
            envelope.ciphertext,
            associated_data,
        )

    except (ValueError, TypeError) as exc:
        raise EnvelopeDecryptionError(
            "Unable to decrypt or authenticate "
            "the message envelope."
        ) from exc

    except Exception as exc:
        raise EnvelopeDecryptionError(
            "Unable to decrypt or authenticate "
            "the message envelope."
        ) from exc