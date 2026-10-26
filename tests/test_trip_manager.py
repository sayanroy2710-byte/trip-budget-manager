import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

# Use an in-memory or test database
os.environ["DATABASE_URL"] = "sqlite:///./test_tripbudget.db"

from app.main import app
from app.database import init_db

client = TestClient(app)


def setup_module():
    init_db()


def teardown_module():
    if os.path.exists("./test_tripbudget.db"):
        try:
            os.remove("./test_tripbudget.db")
        except Exception:
            pass


def test_landing_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "Trip Budget Manager" in res.text


def test_create_trip():
    payload = {
        "name": "Goa Beach Trip",
        "currency": "₹",
        "description": "Weekend getaway with college friends",
        "members": ["Rahul", "Priya", "Amit"]
    }
    res = client.post("/api/trips", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Goa Beach Trip"
    assert data["currency"] == "₹"
    assert len(data["members"]) == 3
    assert "id" in data


def test_trip_full_workflow():
    # 1. Create Trip
    res = client.post("/api/trips", json={
        "name": "Manali Trek",
        "currency": "₹",
        "members": ["Alice", "Bob", "Charlie"]
    })
    assert res.status_code == 201
    trip_data = res.json()
    trip_id = trip_data["id"]
    members = trip_data["members"]
    alice_id = next(m["id"] for m in members if m["name"] == "Alice")
    bob_id = next(m["id"] for m in members if m["name"] == "Bob")
    charlie_id = next(m["id"] for m in members if m["name"] == "Charlie")

    # 2. Add Member (David)
    res = client.post(f"/api/trips/{trip_id}/members", json={"name": "David"})
    assert res.status_code == 201
    david_id = res.json()["id"]

    # 3. Add Expense 1: Alice pays 400 for Hotel (Split equally among Alice, Bob, Charlie, David = 100 each)
    res = client.post(f"/api/trips/{trip_id}/expenses", json={
        "title": "Hotel Stay",
        "amount": 400.0,
        "category": "Stay",
        "paid_by_id": alice_id,
        "split_type": "equal"
    })
    assert res.status_code == 201
    exp1 = res.json()
    assert exp1["amount"] == 400.0
    assert len(exp1["splits"]) == 4

    # 4. Add Expense 2: Bob pays 150 for Cab (Split only between Bob and Charlie = 75 each)
    res = client.post(f"/api/trips/{trip_id}/expenses", json={
        "title": "Cab to Solang",
        "amount": 150.0,
        "category": "Travel",
        "paid_by_id": bob_id,
        "split_type": "equal",
        "split_member_ids": [bob_id, charlie_id]
    })
    assert res.status_code == 201

    # 5. Add Expense 3: Custom split - Charlie pays 100 for Dinner (Alice 20, Bob 30, Charlie 30, David 20)
    res = client.post(f"/api/trips/{trip_id}/expenses", json={
        "title": "Dinner Cafe",
        "amount": 100.0,
        "category": "Food",
        "paid_by_id": charlie_id,
        "split_type": "exact",
        "custom_splits": [
            {"member_id": alice_id, "amount": 20.0},
            {"member_id": bob_id, "amount": 30.0},
            {"member_id": charlie_id, "amount": 30.0},
            {"member_id": david_id, "amount": 20.0}
        ]
    })
    assert res.status_code == 201

    # 6. Fetch Dashboard & Verify Balances
    # Alice: Paid 400. Share: 100 (hotel) + 20 (dinner) = 120. Net = +280
    # Bob: Paid 150. Share: 100 (hotel) + 75 (cab) + 30 (dinner) = 205. Net = -55
    # Charlie: Paid 100. Share: 100 (hotel) + 75 (cab) + 30 (dinner) = 205. Net = -105
    # David: Paid 0. Share: 100 (hotel) + 20 (dinner) = 120. Net = -120
    # Sum of debts: 55 + 105 + 120 = 280 == Alice's credit (280)
    dash_res = client.get(f"/api/trips/{trip_id}")
    assert dash_res.status_code == 200
    dash = dash_res.json()

    assert dash["total_spent"] == 650.0
    assert dash["expense_count"] == 3
    assert dash["member_count"] == 4

    balance_map = {b["member_name"]: b["net_balance"] for b in dash["balances"]}
    assert balance_map["Alice"] == 280.0
    assert balance_map["Bob"] == -55.0
    assert balance_map["Charlie"] == -105.0
    assert balance_map["David"] == -120.0

    # Verify Debt Settlement Plan:
    # All 3 debtors (David 120, Charlie 105, Bob 55) should pay Alice (280 total)
    plan = dash["settlement_plan"]
    assert len(plan) == 3
    plan_total = sum(step["amount"] for step in plan)
    assert plan_total == 280.0
    for step in plan:
        assert step["to_member_name"] == "Alice"

    # 7. Record Settlement: David pays Alice 120
    settle_res = client.post(f"/api/trips/{trip_id}/settlements", json={
        "from_member_id": david_id,
        "to_member_id": alice_id,
        "amount": 120.0,
        "notes": "UPI Payment"
    })
    assert settle_res.status_code == 201
    settle_data = settle_res.json()
    settle_id = settle_data["id"]

    # Re-verify dashboard after David's settlement:
    # David should now be settled (net = 0), Alice remaining credit = 160
    dash2 = client.get(f"/api/trips/{trip_id}").json()
    b2_map = {b["member_name"]: (b["net_balance"], b["status"]) for b in dash2["balances"]}
    assert b2_map["David"] == (0.0, "settled")
    assert b2_map["Alice"][0] == 160.0

    # 8. Undo settlement
    undo_res = client.delete(f"/api/trips/{trip_id}/settlements/{settle_id}")
    assert undo_res.status_code == 200

    # 9. Test WhatsApp Export
    wa_res = client.get(f"/api/trips/{trip_id}/export/whatsapp")
    assert wa_res.status_code == 200
    assert "MANALI TREK" in wa_res.json()["text"]
    assert "Alice" in wa_res.json()["text"]

    # 10. Test CSV Export
    csv_res = client.get(f"/api/trips/{trip_id}/export/csv")
    assert csv_res.status_code == 200
    assert "Hotel Stay" in csv_res.text
    assert "Cab to Solang" in csv_res.text

    # 11. Test Web Page Rendering
    page_res = client.get(f"/trip/{trip_id}")
    assert page_res.status_code == 200
    assert "Manali Trek" in page_res.text
