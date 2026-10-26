from typing import List, Dict, Any


def calculate_balances(
    members: List[Any],
    expenses: List[Any],
    settlements: List[Any]
) -> List[Dict[str, Any]]:
    """
    Computes total paid, total share consumed, and net balance for each member in the trip.
    Takes into account expenses and existing recorded settlements.
    """
    balance_map = {}
    for member in members:
        balance_map[member.id] = {
            "member_id": member.id,
            "member_name": member.name,
            "color": member.color or "#3B82F6",
            "total_paid": 0.0,
            "total_share": 0.0,
            "net_balance": 0.0,
            "status": "settled",
        }

    # Process all expenses
    for expense in expenses:
        if expense.paid_by_id in balance_map:
            balance_map[expense.paid_by_id]["total_paid"] += float(expense.amount)

        for split in expense.splits:
            if split.member_id in balance_map:
                balance_map[split.member_id]["total_share"] += float(split.amount)

    # Process settlements already made
    for settlement in settlements:
        # Payer settled money: their paid amount increases (they contributed to clearing debt)
        if settlement.from_member_id in balance_map:
            balance_map[settlement.from_member_id]["total_paid"] += float(settlement.amount)

        # Receiver received money: their consumption share increases (they received payback)
        if settlement.to_member_id in balance_map:
            balance_map[settlement.to_member_id]["total_share"] += float(settlement.amount)

    result = []
    for member_id, data in balance_map.items():
        paid = round(data["total_paid"], 2)
        share = round(data["total_share"], 2)
        net = round(paid - share, 2)

        if net > 0.01:
            status = "creditor"  # gets back money
        elif net < -0.01:
            status = "debtor"    # owes money
        else:
            status = "settled"   # even
            net = 0.0

        result.append({
            "member_id": member_id,
            "member_name": data["member_name"],
            "color": data["color"],
            "total_paid": paid,
            "total_share": share,
            "net_balance": net,
            "status": status,
        })

    return result


def calculate_settlement_plan(balances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Greedy Min-Cash-Flow Algorithm:
    Determines the minimal number of direct transactions to settle all debts.
    Returns: List of {"from_member_id", "from_member_name", "to_member_id", "to_member_name", "amount"}
    """
    # Separate into debtors (owe money, balance < 0) and creditors (get back money, balance > 0)
    debtors = []
    creditors = []

    for b in balances:
        net = b["net_balance"]
        if net < -0.01:
            # store debt as positive number
            debtors.append({
                "id": b["member_id"],
                "name": b["member_name"],
                "amount": abs(net)
            })
        elif net > 0.01:
            creditors.append({
                "id": b["member_id"],
                "name": b["member_name"],
                "amount": net
            })

    transactions = []

    # Sort descending by amount to minimize transaction count
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)

    i = 0  # debtor pointer
    j = 0  # creditor pointer

    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]

        settle_amt = round(min(debtor["amount"], creditor["amount"]), 2)

        if settle_amt > 0.01:
            transactions.append({
                "from_member_id": debtor["id"],
                "from_member_name": debtor["name"],
                "to_member_id": creditor["id"],
                "to_member_name": creditor["name"],
                "amount": settle_amt,
            })

        debtor["amount"] = round(debtor["amount"] - settle_amt, 2)
        creditor["amount"] = round(creditor["amount"] - settle_amt, 2)

        if debtor["amount"] <= 0.01:
            i += 1
        if creditor["amount"] <= 0.01:
            j += 1

    return transactions


def format_whatsapp_summary(
    trip_name: str,
    currency: str,
    total_spent: float,
    balances: List[Dict[str, Any]],
    settlement_plan: List[Dict[str, Any]]
) -> str:
    """
    Formats a clean, ready-to-share WhatsApp trip settlement report with emojis.
    """
    lines = [
        f"🌴 *{trip_name.upper()}* 🌴",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 *Total Trip Spending:* {currency}{total_spent:,.2f}",
        f"👥 *Total Members:* {len(balances)}",
        "",
        "📊 *INDIVIDUAL SUMMARY:*",
    ]

    for b in balances:
        name = b["member_name"]
        paid = b["total_paid"]
        share = b["total_share"]
        net = b["net_balance"]

        if net > 0.01:
            status_text = f"🟢 Gets back {currency}{net:,.2f}"
        elif net < -0.01:
            status_text = f"🔴 Owes {currency}{abs(net):,.2f}"
        else:
            status_text = "⚪ All settled up"

        lines.append(f"• *{name}*: Paid {currency}{paid:,.2f} | Share {currency}{share:,.2f} ➜ {status_text}")

    lines.append("")
    lines.append("🤝 *FINAL SETTLEMENT PLAN:*")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")

    if not settlement_plan:
        lines.append("🎉 *Everyone is completely settled up! No pending payments.*")
    else:
        for idx, step in enumerate(settlement_plan, 1):
            lines.append(
                f"{idx}. 👉 *{step['from_member_name']}* pays *{step['to_member_name']}* ➜ *{currency}{step['amount']:,.2f}*"
            )

    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("✨ Generated by Trip Budget Manager ✨")

    return "\n".join(lines)
