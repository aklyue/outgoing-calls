import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.outgoing_calls.database.postgres.models.base import BaseModel

if TYPE_CHECKING:
    from api.outgoing_calls.database.postgres.models.call import Call

class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(nullable=False)
    fullname: Mapped[str] = mapped_column(nullable=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(default="user") # "admin" или "user"

    calls: Mapped[List["Call"]] = relationship("Call", back_populates="user")
