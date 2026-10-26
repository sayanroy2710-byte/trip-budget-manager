import csv
import io
import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.models import Trip, TripMember, Expense, ExpenseSplit, Settlement
from app.schemas import (
    TripCreate,
    TripOut,
    MemberCreate,
    MemberOut,
    ExpenseCreate,
    ExpenseOut,
    SplitOut,
    SettlementCreate,
    SettlementOut,
    TripDashboardData,
)
from app.settlement import (
    calculate_balances,
    calculate_settlement_plan,
    format_whatsapp_summary,
)

AVATAR_COLORS = [
    "#3B82F6",  # Blue
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#8B5CF6",  # Purple
    "#06B6D4",  # Cyan
    "#F97316",  # Orange
    "#14B8A6",  # Teal
    "#6366F1",  # Indigo
    "#84CC16",  # Lime
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application start
    init_db()
    yield


app = FastAPI(
    title="Trip Budget Manager",
    description="Collaborative group trip expense splitting & debt settlement app",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware (permits local network & online mobile access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ==========================================
# Frontend HTML Routes
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page: create a new trip or open an existing trip."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/trip/{trip_id}", response_class=HTMLResponse)
async def trip_page(trip_id: str, request: Request, db: Session = Depends(get_db)):
    """Main collaborative trip dashboard for mobile and desktop."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": f"Trip '{trip_id}' not found. Please create one or check your link."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request=request,
        name="trip.html",
        context={"trip": trip},
    )


@app.get("/manifest.json")
async def manifest():
    """PWA Web App Manifest for mobile installation."""
    return {
        "name": "Trip Budget Manager",
        "short_name": "TripBudget",
        "description": "Split trip expenses and settle dues with friends",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0F172A",
        "theme_color": "#2563EB",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    }


# ==========================================
# REST API Endpoints
# ==========================================
@app.post("/api/trips", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)):
    """Create a new trip with initial members."""
    # Deduplicate member names preserving order
    clean_members = []
    seen = set()
    for m in payload.members:
        name = m.strip()
        if name and name.lower() not in seen:
            clean_members.append(name)
            seen.add(name.lower())

    if len(clean_members) < 1:
        raise HTTPException(status_code=400, detail="Trip must have at least one member.")

    trip = Trip(
        name=payload.name.strip(),
        currency=payload.currency.strip() if payload.currency else "₹",
        description=payload.description.strip() if payload.description else None,
    )
    db.add(trip)
    db.flush()

    for idx, name in enumerate(clean_members):
        color = AVATAR_COLORS[idx % len(AVATAR_COLORS)]
        member = TripMember(trip_id=trip.id, name=name, color=color)
        db.add(member)

    db.commit()
    db.refresh(trip)
    return trip


@app.get("/api/trips/{trip_id}", response_model=TripDashboardData)
def get_trip_dashboard(trip_id: str, db: Session = Depends(get_db)):
    """Fetches full trip state: members, expenses, calculated balances, and optimal settlement plan."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    members = trip.members
    expenses = trip.expenses
    settlements = trip.settlements

    member_map = {m.id: m.name for m in members}

    # Format expense list
    formatted_expenses = []
    total_spent = 0.0
    for exp in expenses:
        total_spent += float(exp.amount)
        formatted_splits = [
            SplitOut(
                id=s.id,
                member_id=s.member_id,
                member_name=member_map.get(s.member_id, "Unknown"),
                amount=round(float(s.amount), 2),
            )
            for s in exp.splits
        ]
        formatted_expenses.append(
            ExpenseOut(
                id=exp.id,
                trip_id=exp.trip_id,
                title=exp.title,
                amount=round(float(exp.amount), 2),
                category=exp.category or "Food",
                paid_by_id=exp.paid_by_id,
                paid_by_name=member_map.get(exp.paid_by_id, "Unknown"),
                date=exp.date,
                notes=exp.notes,
                splits=formatted_splits,
            )
        )

    # Format settlements
    formatted_settlements = [
        SettlementOut(
            id=s.id,
            trip_id=s.trip_id,
            from_member_id=s.from_member_id,
            from_member_name=member_map.get(s.from_member_id, "Unknown"),
            to_member_id=s.to_member_id,
            to_member_name=member_map.get(s.to_member_id, "Unknown"),
            amount=round(float(s.amount), 2),
            date=s.date,
            notes=s.notes,
        )
        for s in settlements
    ]

    # Calculate Balances & Debt Minimization Plan
    balances = calculate_balances(members, expenses, settlements)
    settlement_plan = calculate_settlement_plan(balances)

    return {
        "trip": trip,
        "total_spent": round(total_spent, 2),
        "member_count": len(members),
        "expense_count": len(expenses),
        "expenses": formatted_expenses,
        "balances": balances,
        "settlement_plan": settlement_plan,
        "settlements_history": formatted_settlements,
    }


@app.post("/api/trips/{trip_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_trip_member(trip_id: str, payload: MemberCreate, db: Session = Depends(get_db)):
    """Add a new member to an existing trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    existing_names = {m.name.lower() for m in trip.members}
    clean_name = payload.name.strip()
    if clean_name.lower() in existing_names:
        raise HTTPException(status_code=400, detail="A member with this name already exists in this trip.")

    color = payload.color or AVATAR_COLORS[len(trip.members) % len(AVATAR_COLORS)]
    member = TripMember(trip_id=trip_id, name=clean_name, color=color)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.post("/api/trips/{trip_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def add_expense(trip_id: str, payload: ExpenseCreate, db: Session = Depends(get_db)):
    """Add an expense and automatically compute member split shares."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    member_ids = {m.id for m in trip.members}
    member_map = {m.id: m.name for m in trip.members}

    if payload.paid_by_id not in member_ids:
        raise HTTPException(status_code=400, detail="Payer is not a registered member of this trip.")

    exp_date = payload.date or datetime.date.today().isoformat()
    expense = Expense(
        trip_id=trip_id,
        title=payload.title.strip(),
        amount=round(payload.amount, 2),
        category=payload.category,
        paid_by_id=payload.paid_by_id,
        date=exp_date,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(expense)
    db.flush()

    total_amount = round(payload.amount, 2)
    splits_to_create = []

    # Handle split logic
    if payload.split_type == "exact" and payload.custom_splits:
        # Validate that custom splits sum up to total amount
        custom_sum = sum(s.amount for s in payload.custom_splits)
        if abs(custom_sum - total_amount) > 0.05:
            raise HTTPException(
                status_code=400,
                detail=f"Sum of custom splits ({custom_sum:.2f}) does not match expense amount ({total_amount:.2f}).",
            )
        for s in payload.custom_splits:
            if s.member_id not in member_ids:
                raise HTTPException(status_code=400, detail=f"Invalid member ID {s.member_id} in splits.")
            splits_to_create.append(
                ExpenseSplit(expense_id=expense.id, member_id=s.member_id, amount=round(s.amount, 2))
            )
    else:
        # Equal split
        participants = payload.split_member_ids if payload.split_member_ids else list(member_ids)
        if not participants:
            raise HTTPException(status_code=400, detail="Must select at least one person to split expense with.")

        for pid in participants:
            if pid not in member_ids:
                raise HTTPException(status_code=400, detail=f"Invalid member ID {pid} in split members.")

        count = len(participants)
        base_share = round(total_amount / count, 2)
        # Handle rounding difference on first member
        remainder = round(total_amount - (base_share * count), 2)

        for idx, pid in enumerate(participants):
            share = round(base_share + (remainder if idx == 0 else 0.0), 2)
            splits_to_create.append(ExpenseSplit(expense_id=expense.id, member_id=pid, amount=share))

    db.add_all(splits_to_create)
    db.commit()
    db.refresh(expense)

    return ExpenseOut(
        id=expense.id,
        trip_id=expense.trip_id,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        paid_by_id=expense.paid_by_id,
        paid_by_name=member_map.get(expense.paid_by_id, "Unknown"),
        date=expense.date,
        notes=expense.notes,
        splits=[
            SplitOut(
                id=s.id,
                member_id=s.member_id,
                member_name=member_map.get(s.member_id, "Unknown"),
                amount=s.amount,
            )
            for s in expense.splits
        ],
    )


@app.delete("/api/trips/{trip_id}/expenses/{expense_id}")
def delete_expense(trip_id: str, expense_id: int, db: Session = Depends(get_db)):
    """Deletes an expense and updates balances."""
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.trip_id == trip_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": "Expense successfully deleted", "id": expense_id}


@app.post("/api/trips/{trip_id}/settlements", response_model=SettlementOut, status_code=status.HTTP_201_CREATED)
def record_settlement(trip_id: str, payload: SettlementCreate, db: Session = Depends(get_db)):
    """Records a settlement payment between members."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    member_ids = {m.id for m in trip.members}
    member_map = {m.id: m.name for m in trip.members}

    if payload.from_member_id not in member_ids or payload.to_member_id not in member_ids:
        raise HTTPException(status_code=400, detail="Invalid member selected for settlement.")

    if payload.from_member_id == payload.to_member_id:
        raise HTTPException(status_code=400, detail="Cannot record settlement to self.")

    settlement = Settlement(
        trip_id=trip_id,
        from_member_id=payload.from_member_id,
        to_member_id=payload.to_member_id,
        amount=round(payload.amount, 2),
        date=payload.date or datetime.date.today().isoformat(),
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return SettlementOut(
        id=settlement.id,
        trip_id=settlement.trip_id,
        from_member_id=settlement.from_member_id,
        from_member_name=member_map.get(settlement.from_member_id, "Unknown"),
        to_member_id=settlement.to_member_id,
        to_member_name=member_map.get(settlement.to_member_id, "Unknown"),
        amount=settlement.amount,
        date=settlement.date,
        notes=settlement.notes,
    )


@app.delete("/api/trips/{trip_id}/settlements/{settlement_id}")
def delete_settlement(trip_id: str, settlement_id: int, db: Session = Depends(get_db)):
    """Deletes (undoes) a recorded settlement payment."""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id, Settlement.trip_id == trip_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement record not found")

    db.delete(settlement)
    db.commit()
    return {"message": "Settlement removed", "id": settlement_id}


@app.get("/api/trips/{trip_id}/export/whatsapp")
def export_whatsapp(trip_id: str, db: Session = Depends(get_db)):
    """Generates ready-to-copy WhatsApp message with formatted trip balances & settlement instructions."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    total_spent = sum(e.amount for e in trip.expenses)
    balances = calculate_balances(trip.members, trip.expenses, trip.settlements)
    settlement_plan = calculate_settlement_plan(balances)

    text = format_whatsapp_summary(
        trip_name=trip.name,
        currency=trip.currency,
        total_spent=total_spent,
        balances=balances,
        settlement_plan=settlement_plan,
    )
    return {"text": text}


@app.get("/api/trips/{trip_id}/export/csv")
def export_csv(trip_id: str, db: Session = Depends(get_db)):
    """Exports all trip expenses as a downloadable CSV spreadsheet."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    member_map = {m.id: m.name for m in trip.members}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Expense ID", "Date", "Title", "Category", "Paid By", f"Total Amount ({trip.currency})", "Splits Breakdown", "Notes"])

    for exp in trip.expenses:
        splits_str = "; ".join(
            [f"{member_map.get(s.member_id, 'Unknown')}: {trip.currency}{s.amount:.2f}" for s in exp.splits]
        )
        writer.writerow([
            exp.id,
            exp.date,
            exp.title,
            exp.category,
            member_map.get(exp.paid_by_id, "Unknown"),
            f"{exp.amount:.2f}",
            splits_str,
            exp.notes or "",
        ])

    output.seek(0)
    filename = f"{trip.name.replace(' ', '_')}_expenses.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
