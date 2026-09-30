from django.test import SimpleTestCase

from messaging.key_exchange import (
    derive_shared_secret,
    generate_x25519_key_pair,
)


class X25519KeyExchangeTests(SimpleTestCase):

    def test_two_parties_derive_same_shared_secret(self):
        alice_private, alice_public = (
            generate_x25519_key_pair()
        )

        bob_private, bob_public = (
            generate_x25519_key_pair()
        )

        alice_shared_secret = derive_shared_secret(
            alice_private,
            bob_public,
        )

        bob_shared_secret = derive_shared_secret(
            bob_private,
            alice_public,
        )

        self.assertEqual(
            alice_shared_secret,
            bob_shared_secret,
        )

    def test_shared_secret_is_not_public_key(self):
        private_key, public_key = (
            generate_x25519_key_pair()
        )

        self.assertNotEqual(
            private_key,
            public_key,
        )

    def test_different_key_pairs_produce_different_secrets(self):
        alice_private, alice_public = (
            generate_x25519_key_pair()
        )

        bob_private, bob_public = (
            generate_x25519_key_pair()
        )

        charlie_private, charlie_public = (
            generate_x25519_key_pair()
        )

        alice_secret = derive_shared_secret(
            alice_private,
            bob_public,
        )

        charlie_secret = derive_shared_secret(
            charlie_private,
            bob_public,
        )

        self.assertNotEqual(
            alice_secret,
            charlie_secret,
        )