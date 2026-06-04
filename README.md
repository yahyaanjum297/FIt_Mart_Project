# FitMart — Gym & Healthcare Platform

A full-stack fitness management platform with AI-powered workout plans, health vitals tracking, doctor integrations, and more.

## 🚀 Quick Start

### Backend (Python/FastAPI)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Edit with your settings
python run.py                 # Starts on http://localhost:8000
```

**API Docs:** http://localhost:8000/docs  
**Health Check:** http://localhost:8000/health

### Frontend

Open `index.html` in a browser, or use Live Server (VS Code extension):

```bash
# With Python
python -m http.server 5500 --directory .

# With Node.js
npx serve . -p 5500
```

Then open: http://localhost:5500

---

## 👥 Demo Accounts

| Role    | Email                 | Password      |
|---------|-----------------------|---------------|
| Admin   | admin@fitmart.pk      | FitMart2025!  |
| Doctor  | doctor@fitmart.pk     | FitMart2025!  |
| Trainer | trainer@fitmart.pk    | FitMart2025!  |
| Member  | ali@fitmart.pk        | FitMart2025!  |

---

## 🏗️ Project Structure

```
fitmart/
├── index.html              # Landing page
├── dashboard.html          # Member dashboard
├── workout-tracker.html    # Workout logging
├── vitals.html             # Health vitals
├── progress-tracking.html  # Body measurements
├── diet.html               # AI diet plans
├── bmi-calculator.html     # BMI calculator
├── plan.html               # AI workout plans
├── appointment.html        # Doctor appointments
├── membership.html         # Plan management
├── schedule.html           # Class schedule
├── reports.html            # Health reports
├── trainers.html           # Trainer directory
├── gym.html                # Gym facilities
├── healthcare.html         # Healthcare services
├── exercise-library.html   # Exercise database
├── workout-plans.html      # Pre-made plans
├── contact.html            # Contact form
├── plans.html              # Pricing plans
├── 404.html                # Error page
│
├── auth-login.html         # Login
├── auth-register.html      # Registration (3-step)
├── auth-forgot.html        # Forgot password
├── auth-reset.html         # Reset password
│
├── admin-dashboard.html    # Admin panel
├── admin-login.html        # Admin login
├── doctor-dashboard.html   # Doctor panel
├── trainer-dashboard.html  # Trainer panel
├── patient.html            # Patient view
│
└── assets/
    ├── styles.css          # Shared design system
    ├── app.js              # Core JS (cursor, API, sync)
    └── nav.js              # Navigation injector
│
└── backend/
    ├── main.py             # FastAPI application
    ├── schema.sql          # PostgreSQL schema
    ├── email_service.py    # Email integration
    ├── workout_planner.cpp # C++ plan generator (source)
    ├── workout.exe         # Compiled binary
    ├── run.py              # Server launcher
    ├── requirements.txt    # Python dependencies
    ├── .env.example        # Environment template
    └── fitmart.db          # SQLite database (auto-created)
```

---

## ⚙️ Features

| Feature | Status | Notes |
|---------|--------|-------|
| User Auth (JWT) | ✅ | Register, Login, Forgot/Reset Password |
| Workout Tracker | ✅ | Sets, reps, weight, calories, notes |
| Health Vitals | ✅ | HR, BP, blood sugar, SpO2, sleep, steps |
| Progress Tracking | ✅ | Weight, body fat, measurements, BMI |
| AI Workout Plans | ✅ | Via Claude API + C++ fallback |
| AI Diet Plans | ✅ | Via Claude API |
| BMI Calculator | ✅ | With health scoring + history |
| Doctor Portal | ✅ | Patient list, notes, appointments |
| Appointments | ✅ | Calendar booking with time slots |
| Admin Dashboard | ✅ | Members, plans, analytics, settings |
| Email Notifications | ✅ | Welcome, reset, appointment, alerts |
| Health Alerts | ✅ | Auto-detected critical vital readings |
| Offline Mode | ✅ | LocalStorage fallback when backend offline |

---

## 🔑 AI Setup (Claude)

1. Get an API key at [console.anthropic.com](https://console.anthropic.com)
2. In **Admin Dashboard → Settings**, paste your `sk-ant-...` key
3. Or in browser console: `FMConfig.setApiKey('sk-ant-...')`

---

## 🛠️ C++ Plan Generator

Build the workout plan binary:

```bash
cd backend
g++ -O2 -std=c++17 -o workout.exe workout_planner.cpp
```

The backend calls `workout.exe` automatically if it exists.

---

## 🗄️ Database

**SQLite** (default): Zero setup, file created automatically at `backend/fitmart.db`

**PostgreSQL** (production):
```bash
createdb fitmart
psql -U postgres -d fitmart -f backend/schema.sql
export DATABASE_URL=postgresql://user:pass@localhost/fitmart
```

---

## 🔒 Security Notes

- Change `SECRET_KEY` in production (32+ random chars)
- Set `allow_origins` in CORS to your domain (not `*`)
- Use HTTPS in production
- Rotate API keys regularly
- Never commit `.env` to git

---

## 📝 License

© 2025 FitMart. All rights reserved.
