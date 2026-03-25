from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
