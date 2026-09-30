from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519


def generate_x25519_key_pair() -> tuple[bytes, bytes]:
    """
    Generate an X25519 private/public key pair.

    Returns:
        tuple:
            private_key_bytes
            public_key_bytes
    """
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return private_key_bytes, public_key_bytes


def derive_shared_secret(
    private_key_bytes: bytes,
    peer_public_key_bytes: bytes,
) -> bytes:
    """
    Derive a shared secret using X25519.

    The same shared secret must be produced by both parties.
    """
    private_key = x25519.X25519PrivateKey.from_private_bytes(
        private_key_bytes
    )

    peer_public_key = x25519.X25519PublicKey.from_public_bytes(
        peer_public_key_bytes
    )

    return private_key.exchange(peer_public_key)