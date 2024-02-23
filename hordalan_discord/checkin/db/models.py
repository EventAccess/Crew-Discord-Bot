from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class DiscordUser(Base):
    __tablename__ = "discord_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[Optional[str]] = mapped_column(String(128))
    checkin: Mapped["CheckinState"] = relationship(
        "CheckinState", back_populates="user"
    )
    checkin_id: Mapped[int] = mapped_column(Integer, ForeignKey("checkin_state.id"))

    def __repr__(self) -> str:
        return f"DiscordUser(id={self.id!r}, discord_id={self.discord_id!r}, name={self.name!r}, display_name={self.display_name!r})"


class CheckinState(Base):
    __tablename__ = "checkin_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_in: Mapped[Optional[Boolean]] = mapped_column(Boolean, index=True, nullable=True)
    message: Mapped[Optional[String]] = mapped_column(String(2048))

    user: Mapped[DiscordUser] = relationship(
        "DiscordUser", back_populates="checkin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"CheckinState(id={self.id!r}, user.name={self.user.name!r}, is_in={self.is_in!r}, message={self.message!r})"
