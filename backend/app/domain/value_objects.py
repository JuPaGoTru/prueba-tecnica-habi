import re
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        normalized = self.value.lower().strip() if self.value else ""
        if not normalized or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("Invalid email address")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class Password:
    """Raw (plain text) password — only used before hashing."""
    value: str

    MIN_LENGTH = 8

    def __post_init__(self):
        if len(self.value) < self.MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.MIN_LENGTH} characters long")
        if not re.search(r"[A-Z]", self.value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", self.value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", self.value):
            raise ValueError("Password must contain at least one digit")


@dataclass(frozen=True)
class BudgetPeriod:
    month: int
    year: int

    def __post_init__(self):
        if not (1 <= self.month <= 12):
            raise ValueError("period_month must be between 1 and 12")
        current_year = datetime.now().year
        if not (2000 <= self.year <= current_year + 10):
            raise ValueError(f"period_year must be a valid year (2000-{current_year + 10})")
