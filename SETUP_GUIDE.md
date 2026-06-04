# FitMart — Complete Setup Guide
**Version 2.0 · Gym + Healthcare Platform**

---

## Project Structure

```
fitmart/
├── index.html              ← Landing page + AI plan generator
├── auth-login.html         ← Login page
├── auth-register.html      ← Multi-step registration
├── dashboard.html          ← User dashboard with charts
├── bmi-calculator.html     ← Full BMI calculator + AI analysis
├── workout-tracker.html    ← Workout logging + progressive overload
├── progress-tracking.html  ← Weight/body measurement charts
├── vitals.html             ← Health vitals logging + alerts
├── diet.html               ← AI meal plan + food logger
├── reports.html            ← Full analytics + export
├── gym.html                ← Gym services + class schedule
├── healthcare.html         ← Healthcare services + appointments
├── doctor-dashboard.html   ← Doctor patient management portal
├── plans.html              ← Membership pricing page
├── assets/
│   ├── styles.css          ← Shared design system
│   ├── app.js              ← Shared JS (cursor, toast, FM storage)
│   └── nav.js              ← Nav injector helper
└── backend/
    ├── main.py             ← FastAPI application (all routes)
    ├── requirements.txt    ← Python dependencies
    └── .env.example        ← Environment variable template
```

---

## Step 1 — Run Frontend Immediately (No Backend Needed)

The frontend works **completely standalone** using browser localStorage.
Everything — workouts, vitals, progress, BMI history — saves locally.

```bash
# Option A: VS Code Live Server (recommended)
# 1. Open the fitmart/ folder in VS Code
# 2. Install the "Live Server" extension
# 3. Right-click index.html → "Open with Live Server"
# → Opens at http://127.0.0.1:5500

# Option B: Python HTTP server
cd fitmart/
python -m http.server 5500
# → Opens at http://localhost:5500

# Option C: Node.js
npx serve fitmart/ -p 5500
```

Open your browser at `http://127.0.0.1:5500` and the full site works.

---

## Step 2 — Add Your Claude API Key (for AI Features)

The AI plan generator, BMI analysis, and diet plan generator all use
the Claude API. Without a key they fall back to a built-in template.

**To enable real AI:**

1. Get your key at **https://console.anthropic.com**
2. Open `assets/app.js`
3. Find this line near the bottom:
   ```javascript
   ANTHROPIC_KEY: 'YOUR_API_KEY_HERE',
   ```
4. Replace with your actual key:
   ```javascript
   ANTHROPIC_KEY: 'sk-ant-api03-...',
   ```

> ⚠️ **Security**: Never commit your API key to Git.
> For production, proxy all Claude API calls through your FastAPI backend
> so the key stays server-side. See Step 4 for the backend proxy route.

---

## Step 3 — Set Up Python Backend

The backend gives you a real database, user authentication, and server-side
data storage so data persists across devices and browsers.

### 3.1 — Install Python 3.11+

```bash
python --version   # Must be 3.8+
```

### 3.2 — Create Virtual Environment

```bash
cd fitmart/backend/
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3.3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### 3.4 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=sqlite:///./fitmart.db    # SQLite — no setup needed
SECRET_KEY=your-random-32-char-string  # Generate: python -c "import secrets; print(secrets.token_hex(16))"
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
```

### 3.5 — Run the Backend

```bash
uvicorn main:app --reload --port 8000
```

The API starts at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 3.6 — Connect Frontend to Backend

In `assets/app.js`, the `FMAPI.BASE` is already set:
```javascript
window.FMAPI = {
  BASE: 'http://127.0.0.1:8000',
  ...
}
```

The login/register forms already try the backend first and fall back to
localStorage if it's not running. No changes needed for development.

---

## Step 4 — Database Options

### Option A: SQLite (Default — Zero Setup)
```env
DATABASE_URL=sqlite:///./fitmart.db
```
The file `fitmart.db` is created automatically on first run.
Perfect for development and small deployments.

### Option B: PostgreSQL (Production Recommended)

**Install PostgreSQL:**
```bash
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows: Download from https://www.postgresql.org/download/windows/

# Mac:
brew install postgresql@16
brew services start postgresql@16
```

**Create database:**
```sql
psql -U postgres
CREATE DATABASE fitmart;
CREATE USER fitmart_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fitmart TO fitmart_user;
\q
```

**Install driver:**
```bash
pip install psycopg2-binary
```

**Set in .env:**
```env
DATABASE_URL=postgresql://fitmart_user:your_password@localhost:5432/fitmart
```

### Option C: MySQL

```bash
pip install pymysql
```
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fitmart
```

---

## Step 5 — Migrate the Access Database

Your original `Fit_Mart_Data_Base.accdb` file needs to be migrated.

### 5.1 — Export from Access

In Microsoft Access:
1. Open `Fit_Mart_Data_Base.accdb`
2. External Data → Export → Text File (CSV) for each table
3. Save all CSVs to `fitmart/backend/migration/`

### 5.2 — Run Migration Script

```python
# fitmart/backend/migrate_access.py
import csv, json
from main import SessionLocal, User, hash_password

db = SessionLocal()

# Example: import users from CSV
with open("migration/users.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing = db.query(User).filter(User.email == row.get('Email','')).first()
        if not existing:
            user = User(
                name=row.get('Name',''),
                email=row.get('Email',''),
                password=hash_password(row.get('Password','fitmart123')),
                role=row.get('Role','member').lower(),
                age=int(row['Age']) if row.get('Age') else None,
                weight=float(row['Weight']) if row.get('Weight') else None,
                height=float(row['Height']) if row.get('Height') else None,
            )
            db.add(user)

db.commit()
print("Migration complete!")
db.close()
```

```bash
python migrate_access.py
```

---

## Step 6 — Compile workout.cpp (C++ Plan Generator)

Your existing `workout.cpp` generates exercise plans. Compile it for the backend.

```bash
# Linux/Mac:
g++ -O2 -o backend/workout workout.cpp

# Windows (MinGW):
g++ -O2 -o backend/workout.exe workout.cpp

# Windows (MSVC):
cl /O2 workout.cpp /Fe:backend/workout.exe
```

The backend's `/generate-plan` endpoint calls `workout.exe` automatically.
If the exe is not found, a Python fallback plan is returned instead.

---

## Step 7 — Production Deployment

### Option A: Railway (Easiest — Free Tier Available)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy backend
cd fitmart/backend/
railway init
railway up

# Set environment variables in Railway dashboard:
# DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY
```

### Option B: Vercel (Frontend) + Railway (Backend)

**Frontend on Vercel:**
```bash
npm install -g vercel
cd fitmart/
vercel --prod
```

**Update API URL in app.js:**
```javascript
BASE: 'https://your-backend.railway.app',
```

### Option C: VPS (Ubuntu) — Full Control

```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip nginx certbot

# Clone your repo
git clone https://github.com/you/fitmart.git /var/www/fitmart

# Backend as systemd service
sudo nano /etc/systemd/system/fitmart.service
```

```ini
[Unit]
Description=FitMart FastAPI Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/fitmart/backend
ExecStart=/var/www/fitmart/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/var/www/fitmart/backend/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fitmart
sudo systemctl start fitmart
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name fitmart.pk www.fitmart.pk;

    # Frontend
    location / {
        root /var/www/fitmart;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx

# SSL (HTTPS)
sudo certbot --nginx -d fitmart.pk -d www.fitmart.pk
```

---

## Step 8 — AWS Deployment (As Per Architecture Diagram)

Your architecture diagram shows:  
**User → AWS → Amazon S3 → Amazon RDS → Query → REST/SOAP API Gateway**

### 8.1 — Amazon RDS (PostgreSQL)

1. AWS Console → RDS → Create Database
2. Engine: PostgreSQL 16
3. Instance: `db.t3.micro` (free tier)
4. DB name: `fitmart`, username: `admin`
5. Note the **endpoint URL**

```env
DATABASE_URL=postgresql://admin:password@your-rds-endpoint.rds.amazonaws.com:5432/fitmart
```

### 8.2 — Amazon S3 (Static Frontend)

```bash
# Install AWS CLI
pip install awscli
aws configure   # Enter your Access Key, Secret, region (ap-south-1)

# Create bucket
aws s3 mb s3://fitmart-frontend

# Upload frontend
aws s3 sync fitmart/ s3://fitmart-frontend --exclude "backend/*"

# Enable static website hosting
aws s3 website s3://fitmart-frontend --index-document index.html
```

### 8.3 — API Gateway + Lambda (Serverless Backend)

Or deploy FastAPI as a Lambda function using Mangum:
```bash
pip install mangum
```

Add to `main.py`:
```python
from mangum import Mangum
handler = Mangum(app)   # Lambda entry point
```

---

## Step 9 — API Key Security for Production

**Never expose your Anthropic API key in frontend JavaScript.**

### Secure Approach: Backend Proxy

Add this route to `backend/main.py`:

```python
import httpx, os

@app.post("/ai/generate-plan")
async def ai_generate_plan(data: PlanRequest):
    """Proxy Claude API call — key stays server-side"""
    bmi = round(data.weight / ((data.height/100)**2), 1)
    prompt = f"""Create a personalized fitness plan for:
    Age: {data.age}, Weight: {data.weight}kg, Height: {data.height}cm, BMI: {bmi}
    Injury: {data.injury}, Condition: {data.disease}
    Goal: {data.goal}, Location: {data.location}
    Respond in 4 clear paragraphs with specific exercises and nutrition advice."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
    data = response.json()
    return {"plan": data["content"][0]["text"]}
```

**Then in frontend**, change the fetch call to:
```javascript
const res = await fetch('http://localhost:8000/ai/generate-plan', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({age, weight, height, injury, disease, goal, location})
});
```

---

## Step 10 — Quick Reference: All API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get JWT token |
| POST | `/workouts/{user_id}` | Log a workout |
| GET | `/workouts/{user_id}` | Get workout history |
| DELETE | `/workouts/{workout_id}` | Delete a workout |
| POST | `/vitals/{user_id}` | Log health vitals |
| GET | `/vitals/{user_id}` | Get vitals history |
| POST | `/progress/{user_id}` | Log body measurements |
| GET | `/progress/{user_id}` | Get progress history |
| POST | `/appointments/{user_id}` | Book appointment |
| GET | `/appointments/{user_id}` | Get appointments |
| GET | `/doctor/patients/{doctor_id}` | Doctor: all patients |
| POST | `/doctor/notes` | Add doctor note |
| GET | `/reports/{user_id}` | Full analytics report |
| POST | `/generate-plan` | C++ workout plan |
| GET | `/docs` | Interactive API docs |

---

## Step 11 — Test User Credentials (Demo)

Once the backend is running, register through the UI or use these demo logins
(these use localStorage fallback — no backend required):

| Email | Role | Password |
|-------|------|----------|
| `doctor@fitmart.pk` | Doctor | any |
| `admin@fitmart.pk` | Admin | any |
| *(any other email)* | Member | any |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error in browser | Add your frontend URL to `allow_origins` in `main.py` |
| `workout.exe` not found | Compile from `workout.cpp` or use the Python fallback |
| AI not responding | Check your API key in `assets/app.js` or `.env` |
| Database not created | Run `uvicorn main:app` once — SQLAlchemy auto-creates tables |
| Port 8000 busy | Change `--port 8000` to `--port 8001` and update `FMAPI.BASE` |
| Live Server not working | Use `python -m http.server 5500` instead |

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3 (custom design system), Vanilla JS |
| Charts | Chart.js 4.4 |
| AI | Anthropic Claude API (claude-sonnet-4) |
| Backend | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose) |
| Database | SQLite (dev) / PostgreSQL or MySQL (prod) |
| Plan Engine | C++ executable (workout.cpp) |
| Hosting | Vercel + Railway / AWS S3 + RDS / VPS |

---

*Built for FitMart · 2025 · Rawalpindi, Punjab, Pakistan*
