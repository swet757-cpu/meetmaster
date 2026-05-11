import unittest

from app.services.email_validator import is_valid_email


class EmailValidatorTest(unittest.TestCase):
    def test_valid_email(self) -> None:
        self.assertTrue(is_valid_email("client@example.com"))

    def test_invalid_email_without_at(self) -> None:
        self.assertFalse(is_valid_email("client.example.com"))

    def test_invalid_email_without_domain(self) -> None:
        self.assertFalse(is_valid_email("client@"))


if __name__ == "__main__":
    unittest.main()

