from django.test import SimpleTestCase

from messaging.key_exchange import (
    generate_x25519_key_pair,
)

from messaging.message_encryption import (
    EncryptedEnvelope,
    EnvelopeDecryptionError,
    InvalidKeyMaterialError,
    decrypt_for_recipient,
    encrypt_for_recipient,
)


class MessageEncryptionTests(SimpleTestCase):

    def setUp(self):
        (
            self.recipient_private,
            self.recipient_public,
        ) = generate_x25519_key_pair()

        (
            self.other_private,
            self.other_public,
        ) = generate_x25519_key_pair()

        self.plaintext = (
            b"Maxfiy WebEmail xabari."
        )

    def test_encrypt_and_decrypt_round_trip(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        decrypted = decrypt_for_recipient(
            envelope,
            self.recipient_private,
        )

        self.assertEqual(
            decrypted,
            self.plaintext,
        )

    def test_envelope_does_not_contain_plaintext(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        self.assertNotIn(
            self.plaintext,
            envelope.ciphertext,
        )

    def test_each_encryption_uses_new_material(self):
        first = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        second = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        self.assertNotEqual(
            first.ephemeral_public_key,
            second.ephemeral_public_key,
        )

        self.assertNotEqual(
            first.nonce,
            second.nonce,
        )

        self.assertNotEqual(
            first.wrap_nonce,
            second.wrap_nonce,
        )

        self.assertNotEqual(
            first.salt,
            second.salt,
        )

    def test_wrong_recipient_cannot_decrypt(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        with self.assertRaises(
            EnvelopeDecryptionError
        ):
            decrypt_for_recipient(
                envelope,
                self.other_private,
            )

    def test_modified_ciphertext_is_rejected(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        modified = bytearray(
            envelope.ciphertext
        )

        modified[0] ^= 1

        tampered = EncryptedEnvelope(
            ciphertext=bytes(modified),
            nonce=envelope.nonce,
            ephemeral_public_key=(
                envelope.ephemeral_public_key
            ),
            salt=envelope.salt,
            wrapped_key=envelope.wrapped_key,
            wrap_nonce=envelope.wrap_nonce,
        )

        with self.assertRaises(
            EnvelopeDecryptionError
        ):
            decrypt_for_recipient(
                tampered,
                self.recipient_private,
            )

    def test_modified_wrapped_key_is_rejected(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        modified = bytearray(
            envelope.wrapped_key
        )

        modified[0] ^= 1

        tampered = EncryptedEnvelope(
            ciphertext=envelope.ciphertext,
            nonce=envelope.nonce,
            ephemeral_public_key=(
                envelope.ephemeral_public_key
            ),
            salt=envelope.salt,
            wrapped_key=bytes(modified),
            wrap_nonce=envelope.wrap_nonce,
        )

        with self.assertRaises(
            EnvelopeDecryptionError
        ):
            decrypt_for_recipient(
                tampered,
                self.recipient_private,
            )

    def test_associated_data_must_match(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
            associated_data=b"message:123",
        )

        with self.assertRaises(
            EnvelopeDecryptionError
        ):
            decrypt_for_recipient(
                envelope,
                self.recipient_private,
                associated_data=b"message:456",
            )

    def test_invalid_public_key_is_rejected(self):
        with self.assertRaises(
            InvalidKeyMaterialError
        ):
            encrypt_for_recipient(
                self.plaintext,
                b"short",
            )

    def test_invalid_private_key_is_rejected(self):
        envelope = encrypt_for_recipient(
            self.plaintext,
            self.recipient_public,
        )

        with self.assertRaises(
            InvalidKeyMaterialError
        ):
            decrypt_for_recipient(
                envelope,
                b"short",
            )