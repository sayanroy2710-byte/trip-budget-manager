# 🚀 Online Deployment & Mobile Access Guide

This guide walks you through deploying your **Trip Budget Manager** online so your friends can open it on their mobile phones from anywhere in the world.

---

## 🌟 Option 1: Free 1-Click Deployment on Render.com (Recommended)

Render offers free hosting with HTTPS and automatic deployments whenever you push to GitHub.

### Step 1: Push your code to GitHub
1. Open PowerShell or Terminal in `C:\PROJECTS\Python Pojects\Budget manager`.
2. Initialize git and commit:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Trip Budget Manager"
   ```
3. Create a new repository on [GitHub](https://github.com/new) (e.g. `trip-budget-manager`).
4. Link and push:
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/trip-budget-manager.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [Render.com](https://render.com) and sign up / log in with your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your `trip-budget-manager` GitHub repository.
4. Fill in the following fields:
   - **Name**: `trip-budget` (or any name you prefer)
   - **Environment**: `Python`
   - **Region**: Closest to you (e.g., Singapore / Frankfurt / Oregon)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
5. Click **Create Web Service**.
6. Render will build the app and give you a free live URL (e.g., `https://trip-budget-xyz.onrender.com`).
7. **Share this link with your trip group on WhatsApp!** Any friend who taps the link can add expenses from their phone.

---

## ⚡ Option 2: Instant Mobile Access via Free Cloudflare Tunnel (No Account/Sign-up needed!)

If you want your friends to access it right now directly from your PC without setting up GitHub or cloud hosting:

1. In PowerShell, download the free `cloudflared` CLI or run:
   ```bash
   winget install --id Cloudflare.cloudflared
   ```
2. Start the Trip Budget Manager on your computer:
   ```powershell
   & .\venv\Scripts\python.exe run.py
   ```
3. In a second PowerShell window, run:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
4. Cloudflare will instantly output a temporary secure HTTPS link (e.g., `https://random-words.trycloudflare.com`).
5. Send that link to your friends. They can open it immediately on mobile 4G/5G/Wi-Fi from anywhere!

---

## 🏠 Option 3: Local Wi-Fi Testing (Same Network)

If everyone on the trip is on the same Wi-Fi or connected to your mobile hotspot:

1. Run the app:
   ```powershell
   & .\venv\Scripts\python.exe run.py
   ```
2. The terminal will display:
   ```
   🚀 TRIP BUDGET MANAGER WEB APP
   ============================================================
   💻 Access from your PC / Browser : http://localhost:8000
   📱 Access from your Mobile Phone: http://192.168.1.XX:8000
   ============================================================
   ```
3. Open `http://192.168.1.XX:8000` in Safari / Chrome on any phone connected to the same Wi-Fi.

---

## 📱 How to Install as an App on Mobile (PWA)

Your web app includes a built-in `manifest.json` and mobile meta tags:

- **On iPhone (Safari)**:
  1. Open the trip URL in Safari.
  2. Tap the **Share** button (box with upward arrow) at the bottom.
  3. Scroll down and tap **"Add to Home Screen"**.
  4. Now it opens like a native app with full screen and no browser address bar!

- **On Android (Chrome)**:
  1. Open the trip URL in Chrome.
  2. Tap the **3 dots menu** in the top right.
  3. Tap **"Install app"** or **"Add to Home screen"**.
