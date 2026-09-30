import os

from django.test import SimpleTestCase

from messaging.crypto_service import (
    AES_KEY_SIZE,
    DecryptionError,
    EncryptedData,
    InvalidKeyError,
    decrypt,
    encrypt,
    generate_key,
)


class CryptoServiceTests(SimpleTestCase):

    def test_generate_key_returns_256_bit_key(self):
        key = generate_key()

        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), AES_KEY_SIZE)

    def test_encrypt_and_decrypt_round_trip(self):
        key = generate_key()
        plaintext = b"Salom, bu maxfiy E-XAT xabari."

        encrypted = encrypt(
            plaintext,
            key,
        )

        decrypted = decrypt(
            encrypted,
            key,
        )

        self.assertEqual(decrypted, plaintext)

    def test_encryption_produces_different_nonce(self):
        key = generate_key()
        plaintext = b"Same message."

        encrypted_1 = encrypt(
            plaintext,
            key,
        )

        encrypted_2 = encrypt(
            plaintext,
            key,
        )

        self.assertNotEqual(
            encrypted_1.nonce,
            encrypted_2.nonce,
        )

    def test_ciphertext_is_not_plaintext(self):
        key = generate_key()
        plaintext = b"Secret message."

        encrypted = encrypt(
            plaintext,
            key,
        )

        self.assertNotEqual(
            encrypted.ciphertext,
            plaintext,
        )

    def test_wrong_key_cannot_decrypt(self):
        key = generate_key()
        wrong_key = generate_key()

        plaintext = b"Secret message."

        encrypted = encrypt(
            plaintext,
            key,
        )

        with self.assertRaises(DecryptionError):
            decrypt(
                encrypted,
                wrong_key,
            )

    def test_modified_ciphertext_is_rejected(self):
        key = generate_key()
        plaintext = b"Secret message."

        encrypted = encrypt(
            plaintext,
            key,
        )

        modified_ciphertext = bytearray(
            encrypted.ciphertext
        )

        modified_ciphertext[0] ^= 1

        modified = EncryptedData(
            nonce=encrypted.nonce,
            ciphertext=bytes(modified_ciphertext),
        )

        with self.assertRaises(DecryptionError):
            decrypt(
                modified,
                key,
            )

    def test_modified_nonce_is_rejected(self):
        key = generate_key()
        plaintext = b"Secret message."

        encrypted = encrypt(
            plaintext,
            key,
        )

        modified_nonce = bytearray(
            encrypted.nonce
        )

        modified_nonce[0] ^= 1

        modified = EncryptedData(
            nonce=bytes(modified_nonce),
            ciphertext=encrypted.ciphertext,
        )

        with self.assertRaises(DecryptionError):
            decrypt(
                modified,
                key,
            )

    def test_invalid_key_length_is_rejected(self):
        invalid_key = os.urandom(16)

        with self.assertRaises(InvalidKeyError):
            encrypt(
                b"Secret message.",
                invalid_key,
            )

    def test_associated_data_must_match(self):
        key = generate_key()
        plaintext = b"Secret message."

        encrypted = encrypt(
            plaintext,
            key,
            associated_data=b"message-id:1",
        )

        with self.assertRaises(DecryptionError):
            decrypt(
                encrypted,
                key,
                associated_data=b"message-id:2",
            )