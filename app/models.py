import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_trip_id():
    """Generates a short, user-friendly 8-character trip identifier."""
    return uuid.uuid4().hex[:8]


def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(32), primary_key=True, default=generate_trip_id, index=True)
    name = Column(String(100), nullable=False)
    currency = Column(String(10), default="₹", nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    members = relationship("TripMember", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan", order_by="desc(Expense.created_at)")
    settlements = relationship("Settlement", back_populates="trip", cascade="all, delete-orphan", order_by="desc(Settlement.created_at)")


class TripMember(Base):
    __tablename__ = "trip_members"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    trip_id = Column(String(32), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), default="#3B82F6")  # Hex color for avatars
    created_at = Column(DateTime, default=get_utc_now)

    trip = relationship("Trip", back_populates="members")
    splits = relationship("ExpenseSplit", back_populates="member", cascade="all, delete-orphan")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    trip_id = Column(String(32), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(30), default="Food")  # Food, Travel, Stay, Activities, Shopping, Other
    paid_by_id = Column(Integer, ForeignKey("trip_members.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    trip = relationship("Trip", back_populates="expenses")
    paid_by = relationship("TripMember", foreign_keys=[paid_by_id])
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("trip_members.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)

    expense = relationship("Expense", back_populates="splits")
    member = relationship("TripMember", back_populates="splits")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    trip_id = Column(String(32), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    from_member_id = Column(Integer, ForeignKey("trip_members.id", ondelete="CASCADE"), nullable=False)
    to_member_id = Column(Integer, ForeignKey("trip_members.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String(10), nullable=False)
    notes = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    trip = relationship("Trip", back_populates="settlements")
    from_member = relationship("TripMember", foreign_keys=[from_member_id])
    to_member = relationship("TripMember", foreign_keys=[to_member_id])
