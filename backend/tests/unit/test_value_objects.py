import pytest
from app.domain.value_objects import Email, Password


class TestEmail:
    def test_valid_email_is_normalized(self):
        email = Email("  User@Example.COM  ")
        assert email.value == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError):
            Email("not-an-email")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError):
            Email("")


class TestPassword:
    def test_valid_password(self):
        pwd = Password("Secure1Pass")
        assert pwd.value == "Secure1Pass"

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 8"):
            Password("Ab1")

    def test_no_uppercase_raises(self):
        with pytest.raises(ValueError, match="uppercase"):
            Password("secure1pass")

    def test_no_lowercase_raises(self):
        with pytest.raises(ValueError, match="lowercase"):
            Password("SECURE1PASS")

    def test_no_digit_raises(self):
        with pytest.raises(ValueError, match="digit"):
            Password("SecurePass")
