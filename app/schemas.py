from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# Member Schemas
class MemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = "#3B82F6"


class MemberCreate(MemberBase):
    pass


class MemberOut(MemberBase):
    id: int
    trip_id: str

    model_config = ConfigDict(from_attributes=True)


# Expense Split Schemas
class SplitInput(BaseModel):
    member_id: int
    amount: float


class SplitOut(BaseModel):
    id: int
    member_id: int
    member_name: Optional[str] = None
    amount: float

    model_config = ConfigDict(from_attributes=True)


# Expense Schemas
class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    category: str = "Food"
    paid_by_id: int
    date: Optional[str] = None
    notes: Optional[str] = None
    split_type: Optional[str] = "equal"
    split_member_ids: Optional[List[int]] = None
    custom_splits: Optional[List[SplitInput]] = None


class ExpenseOut(BaseModel):
    id: int
    trip_id: str
    title: str
    amount: float
    category: str
    paid_by_id: int
    paid_by_name: Optional[str] = None
    date: str
    notes: Optional[str] = None
    splits: List[SplitOut] = []

    model_config = ConfigDict(from_attributes=True)


# Settlement Schemas
class SettlementCreate(BaseModel):
    from_member_id: int
    to_member_id: int
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None
    date: Optional[str] = None


class SettlementOut(BaseModel):
    id: int
    trip_id: str
    from_member_id: int
    from_member_name: Optional[str] = None
    to_member_id: int
    to_member_name: Optional[str] = None
    amount: float
    date: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Trip Schemas
class TripCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    currency: Optional[str] = "₹"
    description: Optional[str] = None
    members: List[str] = Field(..., min_length=1)


class TripOut(BaseModel):
    id: str
    name: str
    currency: str
    description: Optional[str] = None
    members: List[MemberOut] = []

    model_config = ConfigDict(from_attributes=True)


# Settlement Plan & Balances
class MemberBalance(BaseModel):
    member_id: int
    member_name: str
    color: str
    total_paid: float
    total_share: float
    net_balance: float
    status: str  # "creditor" (gets back), "debtor" (owes), "settled"


class SettlementStep(BaseModel):
    from_member_id: int
    from_member_name: str
    to_member_id: int
    to_member_name: str
    amount: float


class TripDashboardData(BaseModel):
    trip: TripOut
    total_spent: float
    member_count: int
    expense_count: int
    expenses: List[ExpenseOut]
    balances: List[MemberBalance]
    settlement_plan: List[SettlementStep]
    settlements_history: List[SettlementOut]
