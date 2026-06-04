# FitMart — Technical Guide
### How API Keys, the Database, and the Backend Work

---

## TABLE OF CONTENTS
1. [How the Claude API Key Works](#1-how-the-claude-api-key-works)
2. [How the Database Works](#2-how-the-database-works)
3. [How the Backend Works](#3-how-the-backend-works)
4. [How Frontend Connects to Backend](#4-how-frontend-connects-to-backend)
5. [Complete Setup — Step by Step](#5-complete-setup--step-by-step)
6. [API Reference — All 40+ Endpoints](#6-api-reference)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. How the Claude API Key Works

### What is an API Key?

An API key is like a **password that identifies your application** to Anthropic's servers.  
Every time FitMart asks Claude AI to generate a workout plan or BMI analysis, it sends:

```
Your Request  ──►  Anthropic Server  ──►  Claude AI  ──►  Response back to FitMart
                   (checks your API key)
```

Without the key, Anthropic rejects the request. With a valid key, Claude responds.

### Where is the key used in FitMart?

FitMart uses Claude AI in **4 places**:

| Page | What it does |
|------|-------------|
| `index.html` | Generates a personalised workout + diet plan |
| `bmi-calculator.html` | Analyses BMI and gives health advice |
| `diet.html` | Creates a personalised meal plan |
| `plan.html` | Shows the full AI plan result |

### Getting Your Free API Key

1. Go to **https://console.anthropic.com**
2. Sign up (free — no credit card required to start)
3. Click **"API Keys"** → **"Create Key"**
4. Copy the key — it looks like: `sk-ant-api03-ABC123...`
5. You get **free credits** to get started ($5 free on new accounts)

### Where to Put Your Key (3 Options)

---

**Option A — Browser Console (quickest for testing)**
```javascript
// Open browser, press F12, go to Console tab, paste this:
FMConfig.setApiKey('sk-ant-api03-YOUR_KEY_HERE')
// Key is now saved in localStorage. All AI features work immediately.
```

---

**Option B — Admin Dashboard (recommended)**
1. Go to `admin-login.html` → log in
2. Click **Settings & API Keys**
3. Paste your key in the **Claude AI** section → **Save**
4. The key is stored in localStorage and used automatically

---

**Option C — Backend Server (most secure — for production)**

When you run the backend, put your key in `backend/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

The backend then has a `/ai/chat` endpoint that acts as a **proxy**:
```
Browser  ──►  Your FastAPI Server (/ai/chat)  ──►  Anthropic  ──►  Claude
```

**Why is this more secure?**  
The key never leaves your server. Anyone who opens your website's JavaScript
source code cannot see your key. This is **required for production**.

### Key Security Rules

| Rule | Why |
|------|-----|
| Never commit the key to GitHub | Anyone can find it and steal your credits |
| Use backend proxy in production | Key stays server-side, never exposed in browser |
| Rotate keys periodically | If compromised, old key stops working |
| Set usage limits in Anthropic console | Prevents unexpected bills |

### What Happens Without a Key?

FitMart gracefully falls back to **built-in template plans** — every AI feature
still shows a useful result, just not Claude-generated. Users see no error.

---

## 2. How the Database Works

### What is a Database?

A database is a **structured place to store data permanently**. Without it:
- User accounts vanish when you close the browser
- Workouts disappear on page refresh
- Appointments are lost

FitMart uses **SQLAlchemy ORM** — a Python library that lets you write Python
classes instead of raw SQL, and it translates them to database queries automatically.

### Which Database Does FitMart Use?

| Environment | Database | When to Use |
|-------------|----------|-------------|
| Development | **SQLite** | Default. Zero setup. One file: `fitmart.db` |
| Production | **PostgreSQL** | Recommended. Handles thousands of users |
| Alternative | **MySQL** | Works too. Common in shared hosting |

### The Database Tables

FitMart has **9 database tables**. Here is what each one stores:

---

#### `users` — All accounts
```
id | name | email | password (hashed) | role | age | weight | height |
injury | disease | goal | plan | joined_at | is_active
```
- Stores **every user** — members, doctors, trainers, admins
- Passwords are **SHA-256 hashed** — the real password is never stored
- `role` controls what each user can see: `member | doctor | trainer | admin`

---

#### `workout_logs` — Every gym session
```
id | user_id | exercise | muscle | date | sets_json | duration | calories | notes
```
- `sets_json` stores the set data as JSON: `[{"set":1,"reps":10,"weight":60,"rpe":7}]`
- One row = one exercise in one session
- Example: 5 exercises in Monday's session = 5 rows

---

#### `vital_logs` — Health readings
```
id | user_id | heart_rate | bp_systolic | bp_diastolic |
blood_sugar | sleep_hrs | steps | spo2 | recorded_at
```
- Each time a user logs vitals, one row is created
- Used to trigger **health alerts** when readings exceed thresholds

---

#### `progress_logs` — Body measurements over time
```
id | user_id | date | weight | body_fat | bmi |
chest | waist | hips | bicep | thigh | neck
```
- BMI is **auto-calculated by a database trigger** when weight is inserted
- Tracks transformation over weeks and months

---

#### `appointments` — Medical bookings
```
id | user_id | doctor_id | doctor_name | appt_date | appt_time |
appt_type | reason | status | prescription | follow_up_date
```
- `status` goes through: `Pending → Confirmed → Done | Cancelled`

---

#### `doctor_notes` — Clinical notes
```
id | doctor_id | patient_id | note | restrictions | approved_ex |
treatment_plan | next_review | created_at
```
- Doctors write notes visible to the patient and trainer
- `restrictions` is a JSON list of banned exercises

---

#### `memberships` — Payment records
```
id | user_id | plan | billing_cycle | amount_pkr |
start_date | end_date | auto_renew | payment_method
```

---

#### `food_logs` — Daily nutrition tracking
```
id | user_id | log_date | meal_type | food_name |
calories | protein_g | carbs_g | fat_g | quantity
```

---

#### `health_alerts` — Automatic alerts
```
id | user_id | alert_type | value | threshold | severity |
message | acknowledged | created_at
```
- Created automatically when vital readings exceed safe ranges
- `severity`: `warning | critical`

---

### Database Relationships

```
users (1) ──────────────────── (many) workout_logs
users (1) ──────────────────── (many) vital_logs
users (1) ──────────────────── (many) progress_logs
users (1) ──────────────────── (many) appointments
users (1) ──────────────────── (many) food_logs
users (1) ──────────────────── (many) health_alerts
users (doctor) (1) ─────────── (many) doctor_notes (for patient)
```

### How Data Flows — Example: Logging a Workout

```
1. User fills workout form in workout-tracker.html
2. JavaScript calls: FM.addWorkout(entry)       ← saves to localStorage first
3. JavaScript calls: FMSync.saveWorkout(entry)  ← also POSTs to backend
4. Backend /workouts/{user_id} receives the data
5. SQLAlchemy creates a WorkoutLog object
6. db.add(entry); db.commit() writes to the database
7. Data now lives in the workouts table permanently
8. Next time user opens the site, GET /workouts/{user_id} fetches it back
```

### Viewing Your Database

**SQLite** (development):
```bash
# Install SQLite browser (free): https://sqlitebrowser.org
# Open fitmart.db in the app — browse all tables visually

# Or command line:
sqlite3 fitmart.db
.tables                    # list all tables
SELECT * FROM users;       # view users
SELECT * FROM workout_logs WHERE user_id=1;
.quit
```

**PostgreSQL** (production):
```bash
psql -U fitmart_user -d fitmart
\dt                        # list tables
SELECT name, plan, joined_at FROM users ORDER BY joined_at DESC;
\q
```

---

## 3. How the Backend Works

### What is FastAPI?

FastAPI is a **Python web framework** that turns your Python functions into
HTTP API endpoints that the browser can call.

```
Browser (JavaScript fetch)  ──►  FastAPI Route  ──►  Database  ──►  Response
```

### Project Structure

```
backend/
├── main.py              ← All routes and logic (1052 lines)
│   ├── Database models  ← Python classes = database tables
│   ├── Schemas          ← Pydantic models = request validation
│   ├── Auth routes      ← /auth/login, /auth/register
│   ├── Member routes    ← /workouts, /vitals, /progress
│   ├── Doctor routes    ← /doctor/patients, /doctor/notes
│   ├── Admin routes     ← /admin/plans, /admin/settings
│   ├── AI proxy route   ← /ai/chat
│   └── Analytics route  ← /reports, /admin/analytics
├── email_service.py     ← Email sending (welcome, alerts, reset)
├── migrate_access.py    ← Import old Access DB data
├── schema.sql           ← PostgreSQL production schema
├── requirements.txt     ← Python packages needed
└── .env.example         ← Environment variables template
```

### How Authentication Works

FitMart uses **JWT (JSON Web Tokens)** for authentication:

```
1. User sends: POST /auth/login  {email, password}
2. Backend checks: hash(password) == stored hash?
3. If yes, backend creates a JWT token:
   {sub: user_id, role: "member", exp: 7 days from now}
   Signed with SECRET_KEY — cannot be forged
4. Token sent back to browser
5. Browser stores token in localStorage
6. Every future request includes: Authorization: Bearer <token>
7. Backend verifies token on protected routes
```

**Why hashing?** If your database is ever leaked, hackers get `a3f2b1c4...` 
(the hash) — not the actual password. Hashes cannot be reversed.

### How a Request Goes Through the System

Taking `POST /workouts/1` as an example:

```python
# 1. REQUEST arrives from browser:
#    POST http://localhost:8000/workouts/1
#    Body: {"exercise":"Bench Press","muscle":"Chest","date":"2025-12-20",...}

@app.post("/workouts/{user_id}", status_code=201)
def add_workout(user_id: int, data: WorkoutIn, db: Session = Depends(get_db)):

    # 2. VALIDATION — Pydantic checks the request body matches WorkoutIn schema
    #    If "exercise" is missing → 422 error returned automatically
    
    # 3. DATABASE — Create the record
    entry = WorkoutLog(
        user_id=user_id,
        exercise=data.exercise,        # "Bench Press"
        muscle=data.muscle,            # "Chest"
        date=data.date,                # "2025-12-20"
        sets_json=json.dumps(data.sets), # "[{set:1,reps:10,weight:60}]"
        calories=data.calories,
    )
    db.add(entry)      # Stage the insert
    db.commit()        # Execute: INSERT INTO workout_logs ...
    db.refresh(entry)  # Get the auto-generated ID back
    
    # 4. RESPONSE — Return JSON
    return {"id": entry.id, "message": "Workout logged"}
    # Browser receives: {"id": 42, "message": "Workout logged"}
```

### Running the Backend

```bash
cd fitmart/backend/

# 1. Create virtual environment (only once)
python -m venv venv

# 2. Activate it
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate              # Windows

# 3. Install packages (only once)
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env and fill in:
#   DATABASE_URL=sqlite:///./fitmart.db
#   SECRET_KEY=any-random-string-here
#   ANTHROPIC_API_KEY=sk-ant-api03-...

# 5. Start the server
uvicorn main:app --reload --port 8000

# Backend is now running at http://localhost:8000
# Interactive API docs at http://localhost:8000/docs
```

### The `--reload` Flag

`--reload` means **the server automatically restarts** when you edit `main.py`.
You do not need to manually stop and restart it during development.

---

## 4. How Frontend Connects to Backend

The frontend and backend communicate via **HTTP fetch() calls** in JavaScript.

### The Connection Layer (`assets/app.js`)

```javascript
// FMAPI is the connection bridge defined in app.js
window.FMAPI = {
    BASE: 'http://127.0.0.1:8000',   // ← your backend URL
    
    async post(path, data) {
        const res = await fetch(this.BASE + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    
    async get(path) {
        const res = await fetch(this.BASE + path);
        return res.json();
    }
};
```

### Offline-First Design

FitMart works **even without the backend** — this is called offline-first:

```javascript
// FMSync.saveWorkout — from assets/app.js
async saveWorkout(entry) {
    FM.addWorkout(entry);          // 1. ALWAYS save to localStorage first
                                   //    (works even if server is down)
    if (!user?.id) return entry;   // 2. No user ID = no backend sync needed
    try {
        const res = await FMAPI.post('/workouts/' + user.id, entry);
        return { ...entry, serverId: res.id };   // 3. Also save to database
    } catch {
        return entry;              // 4. If backend is down, no crash — localStorage has it
    }
}
```

### Changing the Backend URL

If your backend runs on a different URL (e.g., Railway or AWS):

```javascript
// In browser console (one time):
localStorage.setItem('fm_backend_url', 'https://your-backend.railway.app')

// Or in Admin Dashboard → Settings → Backend URL field
```

### CORS — Why It's Needed

When the browser at `localhost:5500` tries to call `localhost:8000`, the browser
blocks it by default for security. **CORS** tells the server which origins are allowed:

```python
# In main.py — already configured
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",   # ← your Live Server URL
        "http://localhost:5500",    # ← alternate
        "*",                        # ← allows all (remove in production!)
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**In production**, replace `"*"` with your actual frontend domain:
```python
allow_origins=["https://fitmart.pk", "https://www.fitmart.pk"]
```

---

## 5. Complete Setup — Step by Step

### Step 1 — Open the Frontend (No Setup Needed)

```bash
cd fitmart/
python -m http.server 5500
# Open http://localhost:5500
```

Everything works using browser localStorage. Try:
- Registering an account
- Logging a workout  
- Using the BMI calculator (AI falls back to templates without a key)

---

### Step 2 — Add Your Claude API Key

```javascript
// Press F12 in your browser → Console tab → paste:
FMConfig.setApiKey('sk-ant-api03-YOUR_KEY_HERE')
```

Now all AI features are live. Test by filling the plan generator on the homepage.

---

### Step 3 — Start the Backend

```bash
cd fitmart/backend/
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set SECRET_KEY and ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs — you'll see all 40+ API endpoints.

---

### Step 4 — Test the Connection

In the browser console:
```javascript
// Should print the API status
fetch('http://localhost:8000/').then(r=>r.json()).then(console.log)
// Expected: {status: "FitMart API running", version: "2.0.0"}
```

Or in Admin Dashboard → Settings → click **"Test Connection"**.

---

### Step 5 — Access Admin Panel

1. Open `http://localhost:5500/admin-login.html`
2. Email: `admin@fitmart.pk`  Password: `FitMart@Admin2025`
3. PIN: `1234`
4. 2FA Code: `123456`

In the admin panel you can:
- **Edit membership plans** — change names, prices, features
- **Manage members** — change plans, suspend accounts
- **Configure API keys** — set Claude AI key
- **View analytics** — revenue, registrations, popular exercises
- **Manage health alerts** — see critical readings

---

### Step 6 — Use PostgreSQL for Production

```bash
# Install PostgreSQL
sudo apt install postgresql    # Ubuntu
brew install postgresql@16     # Mac

# Create database
psql -U postgres
CREATE DATABASE fitmart;
CREATE USER fitmart_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fitmart TO fitmart_user;
\q

# Install driver
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://fitmart_user:your_password@localhost:5432/fitmart

# Create all tables (FastAPI does this automatically on first run)
uvicorn main:app --reload
```

---

## 6. API Reference

All endpoints available at `http://localhost:8000/docs` (Swagger UI).

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Login, returns JWT token |
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/reset-password` | Set new password with token |

### Member Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workouts/{user_id}` | Log a workout |
| GET | `/workouts/{user_id}` | Get workout history |
| DELETE | `/workouts/{id}` | Delete a workout |
| POST | `/vitals/{user_id}` | Log health vitals |
| GET | `/vitals/{user_id}` | Get vitals history |
| POST | `/progress/{user_id}` | Log body measurements |
| GET | `/progress/{user_id}` | Get progress history |
| POST | `/food-logs/{user_id}` | Log a meal |
| GET | `/food-logs/{user_id}` | Get food log |
| GET | `/reports/{user_id}` | Full analytics report |
| PATCH | `/users/{user_id}/profile` | Update profile |

### Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/appointments/{user_id}` | Book appointment |
| GET | `/appointments/{user_id}` | Get appointments |
| PATCH | `/appointments/{id}/status` | Update status |
| POST | `/class-bookings/{user_id}` | Book gym class |

### Healthcare
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/doctor/patients/{doctor_id}` | Patient list for doctor |
| POST | `/doctor/notes` | Add clinical note |
| GET | `/doctor/notes/{patient_id}` | Get notes for patient |
| GET | `/alerts/{user_id}` | Get health alerts |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/chat` | Claude AI proxy (key stays server-side) |
| POST | `/generate-plan` | C++ workout plan generator |

### Admin — Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/plans` | Get all plans (public) |
| POST | `/admin/plans/{plan_id}` | Create or update a plan |
| DELETE | `/admin/plans/{plan_id}` | Delete a plan |
| POST | `/admin/plans/reset` | Reset to defaults |

### Admin — Settings & Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/settings` | Get platform settings |
| POST | `/admin/settings` | Save a setting |
| POST | `/admin/settings/bulk` | Save multiple settings |
| GET | `/admin/members` | All members (with filters) |
| PATCH | `/admin/members/{id}` | Update member |
| DELETE | `/admin/members/{id}` | Delete member |
| GET | `/admin/analytics` | Platform statistics |
| GET | `/admin/alerts` | All health alerts |
| GET | `/admin/promos` | Promo codes |
| POST | `/admin/promos` | Create promo |
| PATCH | `/admin/promos/{code}/toggle` | Toggle promo |

---

## 7. Troubleshooting

### "CORS error" in browser console
**Cause:** Frontend origin not in backend's allowed list  
**Fix:** In `main.py`, add your frontend URL to `allow_origins`

### "Failed to fetch" / backend not reachable
**Cause:** Backend not running  
**Fix:**  
```bash
cd fitmart/backend/
uvicorn main:app --reload --port 8000
# Check: http://localhost:8000 in browser — should show API status
```

### AI returns "API Key Not Configured"
**Cause:** No Claude key set  
**Fix:** `FMConfig.setApiKey('sk-ant-api03-...')` in browser console

### "422 Unprocessable Entity" from backend
**Cause:** Request body doesn't match the expected schema  
**Fix:** Check the request body matches the Pydantic model. Visit `/docs` to test.

### Database not found / tables missing
**Cause:** Backend never ran (tables auto-create on first start)  
**Fix:** Run `uvicorn main:app --port 8000` once. SQLAlchemy creates all tables.

### Login works but dashboard says "not logged in"
**Cause:** `fm_user` key in localStorage has wrong role  
**Fix:** `FM.setUser({role:'member', name:'Test', email:'test@test.com'})` in console

### Admin login rejected
**Credentials:**  
- Email: `admin@fitmart.pk`  
- Password: `FitMart@Admin2025`  
- PIN: `1234`  
- 2FA Code: `123456`

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║  FITMART — Quick Reference                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Frontend URL:    http://localhost:5500                        ║
║  Backend URL:     http://localhost:8000                        ║
║  API Docs:        http://localhost:8000/docs                  ║
║  Admin Login:     http://localhost:5500/admin-login.html      ║
╠══════════════════════════════════════════════════════════════╣
║  DEMO CREDENTIALS                                              ║
║  Admin email:     admin@fitmart.pk                            ║
║  Admin pass:      FitMart@Admin2025                           ║
║  Admin PIN:       1234                                         ║
║  Admin 2FA:       123456                                       ║
║  Doctor email:    doctor@fitmart.pk                           ║
║  (any email)  →   member account                              ║
╠══════════════════════════════════════════════════════════════╣
║  SET API KEY (browser console):                               ║
║  FMConfig.setApiKey('sk-ant-api03-YOUR_KEY')                  ║
╠══════════════════════════════════════════════════════════════╣
║  START BACKEND:                                               ║
║  cd backend && uvicorn main:app --reload --port 8000          ║
╚══════════════════════════════════════════════════════════════╝
```
