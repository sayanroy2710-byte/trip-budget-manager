# 🌴 Trip Budget Manager

A modern, responsive, mobile-first group expense splitting and debt settlement web application. Designed for road trips, group vacations, roommates, and events.

---

## ✨ Features

- **📱 Mobile-First Experience**: Clean touch-friendly interface, bottom navigation on phones, responsive cards, and installable PWA support (Add to Home Screen).
- **👥 Collaborative Multi-User Trips**: Share a single trip link or QR code with friends on WhatsApp. Anyone can log their expenses on the go.
- **💸 Flexible Splitting**:
  - Split equally across all trip members.
  - Split equally among selected members only.
  - Exact custom share amounts per member.
- **🤝 Smart Debt Settlement Algorithm**: Uses a greedy cash-flow minimization engine to calculate the absolute minimum number of payments to settle all debts (e.g. "Rahul pays Priya ₹850").
- **✅ Settle Up & Record Payments**: Log settlements as they happen so balances update in real-time.
- **💬 1-Tap WhatsApp Summary**: Generates a formatted breakdown with emojis ready to paste into group chats.
- **📊 Visual Spending Analytics**: Interactive category breakdown doughnut chart and member spending comparison (Chart.js).
- **📥 CSV Export**: Download all expenses as a spreadsheet.
- **⚡ Zero Friction**: No mandatory passwords or complicated logins needed; accessible via unique trip ID or QR code.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, SQLAlchemy
- **Database**: SQLite (local default) / PostgreSQL compatible (via `DATABASE_URL` on cloud)
- **Frontend**: HTML5, Jinja2, Tailwind CSS, Lucide Icons, Chart.js, QRCode.js
- **Deployment**: Render, Railway, Fly.io, or Docker

---

## 🚀 Quick Start (Local Development)

### 1. Activate Virtual Environment
```powershell
cd "C:\PROJECTS\Python Pojects\Budget manager"
.\venv\Scripts\activate
```

### 2. Start the App
```powershell
python run.py
```

The terminal will print:
```text
🚀 TRIP BUDGET MANAGER WEB APP
============================================================
💻 Access from your PC / Browser : http://localhost:8000
📱 Access from your Mobile Phone: http://<your-local-ip>:8000
   (Ensure your phone and PC are connected to the same Wi-Fi)
============================================================
```

---

## 🌐 Online Deployment

See [DEPLOYMENT.md](file:///C:/PROJECTS/Python%20Pojects/Budget%20manager/DEPLOYMENT.md) for 1-click free deployment guides on **Render.com** and **Cloudflare Tunnel**.
