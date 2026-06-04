"""
══════════════════════════════════════════════════════════════
  FITMART — FastAPI Backend v3.1  (Fixed & Production Ready)
  Run:  uvicorn main:app --reload --port 8000
  Docs: http://localhost:8000/docs
══════════════════════════════════════════════════════════════
"""
from fastapi import FastAPI, HTTPException, Depends, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from jose import JWTError, jwt
import json as _json, os, subprocess, hashlib, secrets, re

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
DATABASE_URL   = os.getenv("DATABASE_URL",  "sqlite:///./fitmart.db")
SECRET_KEY     = os.getenv("SECRET_KEY",    "fitmart-dev-secret-change-in-production-2025")
ALGORITHM      = "HS256"
TOKEN_MINUTES  = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))   # 7 days
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
PLANS_FILE     = "plans_data.json"
SETTINGS_FILE  = "settings_data.json"
PROMOS_FILE    = "promos_data.json"

VALID_ROLES    = {"member", "doctor", "trainer", "admin"}
VALID_GOALS    = {"Weight Loss", "Muscle Gain", "Endurance", "Strength", "Flexibility", "General Fitness"}
VALID_LEVELS   = {"Beginner", "Intermediate", "Advanced"}
VALID_LOCATIONS= {"Gym", "Home"}
VALID_GENDERS  = {"Male", "Female", "Other", "Prefer not to say"}

# ══════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enable WAL mode for SQLite for better concurrent read/write
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

class User(Base):
    __tablename__ = "users"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(120), nullable=False)
    email       = Column(String(200), unique=True, index=True, nullable=False)
    password    = Column(String(256), nullable=False)
    role        = Column(String(20),  default="member")
    age         = Column(Integer,  nullable=True)
    gender      = Column(String(30),  nullable=True)
    weight      = Column(Float,   nullable=True)
    height      = Column(Float,   nullable=True)
    injury      = Column(String(255), default="None")
    disease     = Column(String(255), default="None")
    allergies   = Column(String(255), nullable=True)
    goal        = Column(String(50),  default="General Fitness")
    location    = Column(String(20),  default="Gym")
    level       = Column(String(20),  default="Beginner")
    plan        = Column(String(50),  default="Basic")
    is_active   = Column(Boolean, default=True)
    joined_at   = Column(DateTime, default=datetime.utcnow)
    last_login  = Column(DateTime, nullable=True)
    workouts    = relationship("WorkoutLog",   back_populates="user", cascade="all,delete")
    vitals      = relationship("VitalLog",     back_populates="user", cascade="all,delete")
    progress    = relationship("ProgressLog",  back_populates="user", cascade="all,delete")
    appointments = relationship("Appointment", foreign_keys="[Appointment.user_id]", back_populates="user")
    food_logs   = relationship("FoodLog",      back_populates="user", cascade="all,delete")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    exercise  = Column(String(100), nullable=False)
    muscle    = Column(String(50),  default="Other")
    date      = Column(String(10),  nullable=False)
    sets_json = Column(Text,        nullable=False, default="[]")
    duration  = Column(Integer, nullable=True)
    calories  = Column(Integer, nullable=True)
    notes     = Column(Text,    nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
    user      = relationship("User", back_populates="workouts")

class VitalLog(Base):
    __tablename__ = "vital_logs"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    heart_rate   = Column(Float, nullable=True)
    bp_systolic  = Column(Float, nullable=True)
    bp_diastolic = Column(Float, nullable=True)
    blood_sugar  = Column(Float, nullable=True)
    sleep_hrs    = Column(Float, nullable=True)
    steps        = Column(Integer, nullable=True)
    spo2         = Column(Float, nullable=True)
    weight       = Column(Float, nullable=True)
    temperature  = Column(Float, nullable=True)
    notes        = Column(Text,  nullable=True)
    alert_sent   = Column(Boolean, default=False)
    recorded_at  = Column(DateTime, default=datetime.utcnow)
    user         = relationship("User", back_populates="vitals")

class ProgressLog(Base):
    __tablename__ = "progress_logs"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    date      = Column(String(10), nullable=False)
    weight    = Column(Float, nullable=True)
    body_fat  = Column(Float, nullable=True)
    bmi       = Column(Float, nullable=True)
    chest     = Column(Float, nullable=True)
    waist     = Column(Float, nullable=True)
    hips      = Column(Float, nullable=True)
    bicep     = Column(Float, nullable=True)
    thigh     = Column(Float, nullable=True)
    neck      = Column(Float, nullable=True)
    notes     = Column(Text,  nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
    user      = relationship("User", back_populates="progress")

class Appointment(Base):
    __tablename__ = "appointments"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    doctor_name = Column(String(120), nullable=False)
    appt_date   = Column(String(10),  nullable=False)
    appt_time   = Column(String(10),  nullable=True)
    appt_type   = Column(String(30),  default="In-Clinic")
    speciality  = Column(String(60),  nullable=True)
    reason      = Column(Text,        nullable=True)
    status      = Column(String(20),  default="Pending")
    prescription= Column(Text,        nullable=True)
    created_at  = Column(DateTime,    default=datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id], back_populates="appointments")

class FoodLog(Base):
    __tablename__ = "food_logs"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    log_date   = Column(String(10), nullable=False)
    meal_type  = Column(String(30),  nullable=True)
    food_name  = Column(String(150), nullable=False)
    calories   = Column(Integer, nullable=True)
    protein_g  = Column(Float,   nullable=True)
    carbs_g    = Column(Float,   nullable=True)
    fat_g      = Column(Float,   nullable=True)
    fiber_g    = Column(Float,   nullable=True)
    quantity   = Column(String(50), nullable=True)
    logged_at  = Column(DateTime, default=datetime.utcnow)
    user       = relationship("User", back_populates="food_logs")

class DoctorNote(Base):
    __tablename__ = "doctor_notes"
    id           = Column(Integer, primary_key=True, index=True)
    doctor_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    patient_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    note         = Column(Text,  nullable=False)
    restrictions = Column(Text,  nullable=True)
    approved_ex  = Column(Text,  nullable=True)
    treatment_plan = Column(Text, nullable=True)
    next_review  = Column(String(10), nullable=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

class HealthAlert(Base):
    __tablename__ = "health_alerts"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    alert_type   = Column(String(50))
    value        = Column(Float, nullable=True)
    threshold    = Column(Float, nullable=True)
    severity     = Column(String(10), default="warning")
    message      = Column(Text)
    acknowledged = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

class Membership(Base):
    __tablename__ = "memberships"
    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan           = Column(String(50), default="Basic")
    billing_cycle  = Column(String(10), default="monthly")
    amount_pkr     = Column(Integer, nullable=True)
    start_date     = Column(String(10), nullable=False)
    end_date       = Column(String(10), nullable=True)
    auto_renew     = Column(Boolean, default=True)
    is_active      = Column(Boolean, default=True)
    payment_method = Column(String(30), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token      = Column(String(100), unique=True, index=True)
    expires_at = Column(DateTime)
    used       = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# ══════════════════════════════════════════
#  SCHEMAS (Pydantic v2)
# ══════════════════════════════════════════
class UserRegister(BaseModel):
    name:     str
    email:    str
    password: str
    role:     Optional[str] = "member"
    age:      Optional[int] = None
    gender:   Optional[str] = None
    weight:   Optional[float] = None
    height:   Optional[float] = None
    injury:   Optional[str] = "None"
    disease:  Optional[str] = "None"
    allergies:Optional[str] = None
    goal:     Optional[str] = "General Fitness"
    location: Optional[str] = "Gym"
    level:    Optional[str] = "Beginner"
    plan:     Optional[str] = "Basic"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 120:
            raise ValueError("Name too long")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v is not None and (v < 10 or v > 110):
            raise ValueError("Age must be between 10 and 110")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError("Weight must be between 20 and 500 kg")
        return v

    @field_validator("height")
    @classmethod
    def validate_height(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError("Height must be between 50 and 300 cm")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v and v not in VALID_ROLES:
            return "member"
        return v or "member"

class UserLogin(BaseModel):
    email:    str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class WorkoutIn(BaseModel):
    exercise: str
    muscle:   Optional[str] = "Other"
    date:     str
    sets:     list = []
    duration: Optional[int]   = None
    calories: Optional[int]   = None
    notes:    Optional[str]   = None

    @field_validator("exercise")
    @classmethod
    def validate_exercise(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Exercise name required")
        if len(v) > 100: raise ValueError("Exercise name too long")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v):
        if v is not None and (v < 0 or v > 600):
            raise ValueError("Duration must be between 0 and 600 minutes")
        return v

    @field_validator("calories")
    @classmethod
    def validate_calories(cls, v):
        if v is not None and (v < 0 or v > 5000):
            raise ValueError("Calories must be between 0 and 5000")
        return v

class VitalIn(BaseModel):
    heart_rate:   Optional[float] = None
    bp_systolic:  Optional[float] = None
    bp_diastolic: Optional[float] = None
    blood_sugar:  Optional[float] = None
    sleep_hrs:    Optional[float] = None
    steps:        Optional[int]   = None
    spo2:         Optional[float] = None
    weight:       Optional[float] = None
    temperature:  Optional[float] = None
    notes:        Optional[str]   = None

    @field_validator("heart_rate")
    @classmethod
    def validate_hr(cls, v):
        if v is not None and (v < 20 or v > 300):
            raise ValueError("Heart rate must be between 20 and 300 bpm")
        return v

    @field_validator("bp_systolic")
    @classmethod
    def validate_bps(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError("Systolic BP must be between 50 and 300 mmHg")
        return v

    @field_validator("bp_diastolic")
    @classmethod
    def validate_bpd(cls, v):
        if v is not None and (v < 30 or v > 200):
            raise ValueError("Diastolic BP must be between 30 and 200 mmHg")
        return v

    @field_validator("spo2")
    @classmethod
    def validate_spo2(cls, v):
        if v is not None and (v < 50 or v > 100):
            raise ValueError("SpO2 must be between 50 and 100%")
        return v

    @field_validator("sleep_hrs")
    @classmethod
    def validate_sleep(cls, v):
        if v is not None and (v < 0 or v > 24):
            raise ValueError("Sleep hours must be between 0 and 24")
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v):
        if v is not None and (v < 0 or v > 100000):
            raise ValueError("Steps must be between 0 and 100,000")
        return v

class ProgressIn(BaseModel):
    date:     str
    weight:   Optional[float] = None
    body_fat: Optional[float] = None
    chest:    Optional[float] = None
    waist:    Optional[float] = None
    hips:     Optional[float] = None
    bicep:    Optional[float] = None
    thigh:    Optional[float] = None
    neck:     Optional[float] = None
    notes:    Optional[str]   = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class AppointmentIn(BaseModel):
    doctor_name: str
    appt_date:   str
    appt_time:   Optional[str] = None
    appt_type:   Optional[str] = "In-Clinic"
    speciality:  Optional[str] = None
    reason:      Optional[str] = None

    @field_validator("doctor_name")
    @classmethod
    def validate_doctor(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Doctor name required")
        return v

    @field_validator("appt_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            d = datetime.strptime(v, "%Y-%m-%d")
            if d.date() < datetime.utcnow().date():
                raise ValueError("Appointment date cannot be in the past")
        except ValueError as e:
            if "past" in str(e): raise
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("appt_type")
    @classmethod
    def validate_type(cls, v):
        valid = {"In-Clinic", "Video", "Phone"}
        if v and v not in valid:
            return "In-Clinic"
        return v or "In-Clinic"

class FoodLogIn(BaseModel):
    log_date:  Optional[str]   = None
    meal_type: Optional[str]   = None
    food_name: str
    calories:  Optional[int]   = None
    protein_g: Optional[float] = None
    carbs_g:   Optional[float] = None
    fat_g:     Optional[float] = None
    fiber_g:   Optional[float] = None
    quantity:  Optional[str]   = None

    @field_validator("food_name")
    @classmethod
    def validate_food(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Food name required")
        if len(v) > 150: raise ValueError("Food name too long")
        return v

    @field_validator("calories")
    @classmethod
    def validate_cal(cls, v):
        if v is not None and (v < 0 or v > 10000):
            raise ValueError("Calories must be 0–10000")
        return v

class PlanModel(BaseModel):
    id:           str
    name:         str
    price:        int
    priceAnnual:  int
    featured:     bool = False
    features:     list = []
    limits:       dict = {}

class SettingIn(BaseModel):
    key:   str
    value: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Setting key required")
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError("Key must be alphanumeric with _ - . only")
        return v

class AIChatIn(BaseModel):
    prompt:     str
    max_tokens: Optional[int] = 1000

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        v = v.strip()
        if not v: raise ValueError("Prompt cannot be empty")
        if len(v) > 10000: raise ValueError("Prompt too long (max 10,000 chars)")
        return v

class PlanGenerateIn(BaseModel):
    age:      int
    weight:   float
    height:   float
    injury:   Optional[str] = "None"
    disease:  Optional[str] = "None"
    goal:     str
    location: str

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if not (10 <= v <= 110): raise ValueError("Age must be 10–110")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if not (20 <= v <= 500): raise ValueError("Weight must be 20–500 kg")
        return v

    @field_validator("height")
    @classmethod
    def validate_height(cls, v):
        if not (50 <= v <= 300): raise ValueError("Height must be 50–300 cm")
        return v

class ProfileUpdate(BaseModel):
    name:      Optional[str]   = None
    age:       Optional[int]   = None
    gender:    Optional[str]   = None
    weight:    Optional[float] = None
    height:    Optional[float] = None
    injury:    Optional[str]   = None
    disease:   Optional[str]   = None
    goal:      Optional[str]   = None
    location:  Optional[str]   = None
    level:     Optional[str]   = None
    plan:      Optional[str]   = None
    allergies: Optional[str]   = None

# ══════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════
def hash_password(pw: str) -> str:
    salt = "fitmart_salt_2025_v2"
    return hashlib.sha256((pw + salt).encode()).hexdigest()

def verify_password(pw: str, hashed: str) -> bool:
    # Support legacy salt
    if hash_password(pw) == hashed:
        return True
    old_hash = hashlib.sha256((pw + "fitmart_salt_2025").encode()).hexdigest()
    return old_hash == hashed

def create_token(data: dict, expire_minutes: int = TOKEN_MINUTES) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=expire_minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def user_to_dict(u: User) -> dict:
    return {
        "id": u.id, "name": u.name, "email": u.email, "role": u.role,
        "plan": u.plan, "goal": u.goal, "weight": u.weight, "height": u.height,
        "injury": u.injury, "disease": u.disease, "age": u.age,
        "gender": u.gender, "level": u.level, "location": u.location,
        "is_active": u.is_active,
        "joined_at": u.joined_at.isoformat() if u.joined_at else None
    }

def check_alerts(vital: VitalLog, user: User) -> list:
    alerts = []
    if vital.heart_rate:
        if vital.heart_rate < 45:
            alerts.append({"type":"heart_rate","severity":"critical","message":f"🚨 Heart rate {vital.heart_rate} bpm is dangerously low (<45)","value":vital.heart_rate})
        elif vital.heart_rate > 120:
            alerts.append({"type":"heart_rate","severity":"warning","message":f"⚠️ Heart rate {vital.heart_rate} bpm is elevated (>120)","value":vital.heart_rate})
    if vital.bp_systolic:
        if vital.bp_systolic > 180:
            alerts.append({"type":"blood_pressure","severity":"critical","message":f"🚨 Hypertensive crisis: {vital.bp_systolic}/{vital.bp_diastolic} mmHg","value":vital.bp_systolic})
        elif vital.bp_systolic > 140:
            alerts.append({"type":"blood_pressure","severity":"warning","message":f"⚠️ High blood pressure: {vital.bp_systolic}/{vital.bp_diastolic} mmHg","value":vital.bp_systolic})
    if vital.blood_sugar:
        if vital.blood_sugar < 60:
            alerts.append({"type":"blood_sugar","severity":"critical","message":f"🚨 Blood sugar critically low: {vital.blood_sugar} mg/dL (<60)","value":vital.blood_sugar})
        elif vital.blood_sugar > 250:
            alerts.append({"type":"blood_sugar","severity":"critical","message":f"🚨 Blood sugar critically high: {vital.blood_sugar} mg/dL (>250)","value":vital.blood_sugar})
        elif vital.blood_sugar > 180:
            alerts.append({"type":"blood_sugar","severity":"warning","message":f"⚠️ Elevated blood sugar: {vital.blood_sugar} mg/dL","value":vital.blood_sugar})
    if vital.spo2 and vital.spo2 < 92:
        alerts.append({"type":"spo2","severity":"critical","message":f"🚨 SpO2 {vital.spo2}% is critically low (<92%). Seek immediate attention.","value":vital.spo2})
    return alerts

# ══════════════════════════════════════════
#  JSON DATA HELPERS
# ══════════════════════════════════════════
DEFAULT_PLANS = [
    {"id":"basic","name":"Basic","price":0,"priceAnnual":0,"featured":False,
     "features":[{"t":"BMI Calculator","on":True},{"t":"Workout Tracker (10/mo)","on":True},{"t":"Vitals Logger","on":True},{"t":"AI Workout Plans","on":False},{"t":"Doctor Consultations","on":False},{"t":"Progress Analytics","on":False}],
     "limits":{"workoutsPerMonth":10,"doctorConsults":0,"gymClasses":0,"aiPlans":0}},
    {"id":"pro","name":"Pro","price":2999,"priceAnnual":2399,"featured":True,
     "features":[{"t":"Unlimited Workout Tracking","on":True},{"t":"AI Workout Plans","on":True},{"t":"AI Diet Plans","on":True},{"t":"Progress Analytics","on":True},{"t":"Health Vitals + Alerts","on":True},{"t":"2 Doctor Consults/mo","on":True},{"t":"5 Gym Classes/mo","on":True}],
     "limits":{"workoutsPerMonth":999,"doctorConsults":2,"gymClasses":5,"aiPlans":20}},
    {"id":"elite","name":"Elite","price":5999,"priceAnnual":4799,"featured":False,
     "features":[{"t":"Everything in Pro","on":True},{"t":"Unlimited Doctor Consults","on":True},{"t":"Personal Trainer","on":True},{"t":"Monthly Lab Reports","on":True},{"t":"Tele-Medicine Access","on":True},{"t":"4 Physio Sessions/mo","on":True},{"t":"Priority Support 24/7","on":True}],
     "limits":{"workoutsPerMonth":999,"doctorConsults":999,"gymClasses":999,"aiPlans":999}},
]

def load_plans():
    try:
        if os.path.exists(PLANS_FILE):
            with open(PLANS_FILE) as f:
                data = _json.load(f)
                if isinstance(data, list) and len(data) > 0: return data
    except: pass
    return DEFAULT_PLANS.copy()

def save_plans(plans):
    try:
        with open(PLANS_FILE,"w") as f: _json.dump(plans, f, indent=2)
    except Exception as e: print(f"[WARN] plans save: {e}")

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f: return _json.load(f)
    except: pass
    return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE,"w") as f: _json.dump(data, f, indent=2)
    except Exception as e: print(f"[WARN] settings save: {e}")

def load_promos():
    try:
        if os.path.exists(PROMOS_FILE):
            with open(PROMOS_FILE) as f: return _json.load(f)
    except: pass
    return [{"code":"WELCOME20","disc":"20%","plan":"Pro","uses":50,"expires":"2026-12-31","active":True}]

def save_promos(promos):
    try:
        with open(PROMOS_FILE,"w") as f: _json.dump(promos, f, indent=2)
    except: pass

# ══════════════════════════════════════════
#  APP
# ══════════════════════════════════════════
app = FastAPI(
    title="FitMart API",
    description="Gym + Healthcare Platform Backend",
    version="3.1.0"
)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Error handlers ──────────────────────────
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(x) for x in error.get("loc", [])[1:])
        msg = error.get("msg", "Invalid value")
        errors.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(
        status_code=422,
        content={"detail": " | ".join(errors)}
    )

# ── ROOT ─────────────────────────────────
@app.get("/")
def root():
    return {"status":"FitMart API running","version":"3.1.0","docs":"/docs"}

@app.get("/favicon.ico", status_code=204)
def favicon(): pass

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        import sqlalchemy
        db.execute(sqlalchemy.text("SELECT 1"))
        return {"status":"healthy","database":"connected","timestamp":datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status":"unhealthy","database":str(e)}

# ── AUTH ─────────────────────────────────
@app.post("/auth/register", status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        name=data.name, email=data.email, password=hash_password(data.password),
        role=data.role, age=data.age, gender=data.gender,
        weight=data.weight, height=data.height,
        injury=data.injury or "None", disease=data.disease or "None",
        allergies=data.allergies,
        goal=data.goal or "General Fitness",
        location=data.location or "Gym",
        level=data.level or "Beginner",
        plan=data.plan or "Basic",
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_token({"sub": user.id, "role": user.role})
    try:
        from email_service import send_welcome
        send_welcome(user.email, user.name, user.plan)
    except: pass
    return {"token": token, "user": user_to_dict(user)}

@app.post("/auth/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account suspended. Contact support.")
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_token({"sub": user.id, "role": user.role})
    return {"token": token, "user": user_to_dict(user)}

@app.post("/auth/forgot-password")
def forgot_password(body: dict = Body(...), db: Session = Depends(get_db)):
    email = body.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "Email required")
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Invalidate old tokens
        old = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used == False
        ).all()
        for t in old: t.used = True
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(minutes=30)
        reset = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
        db.add(reset); db.commit()
        try:
            from email_service import send_password_reset
            send_password_reset(user.email, user.name, token)
        except: pass
        print(f"[DEV] Reset token for {email}: {token}")
    return {"message": "If that email is registered, a reset link has been sent."}

@app.post("/auth/reset-password")
def reset_password(body: dict = Body(...), db: Session = Depends(get_db)):
    token = body.get("token", "").strip()
    new_password = body.get("new_password", "").strip()
    if not token: raise HTTPException(400, "Token required")
    if len(new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    if not reset:
        raise HTTPException(400, "Invalid or expired reset token")
    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password = hash_password(new_password)
    reset.used = True
    db.commit()
    return {"message": "Password updated successfully"}

@app.patch("/users/{user_id}/profile")
def update_profile(user_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    updates = data.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return {"message": "Profile updated", "user": user_to_dict(user)}

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    return user_to_dict(user)

# ── WORKOUTS ─────────────────────────────
@app.post("/workouts/{user_id}", status_code=201)
def add_workout(user_id: int, data: WorkoutIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    entry = WorkoutLog(
        user_id=user_id, exercise=data.exercise, muscle=data.muscle or "Other",
        date=data.date, sets_json=_json.dumps(data.sets or []),
        duration=data.duration, calories=data.calories, notes=data.notes
    )
    db.add(entry); db.commit(); db.refresh(entry)
    return {"id": entry.id, "message": "Workout logged"}

@app.get("/workouts/{user_id}")
def get_workouts(user_id: int, limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id)\
             .order_by(WorkoutLog.logged_at.desc()).limit(limit).all()
    return [{"id":r.id,"exercise":r.exercise,"muscle":r.muscle,"date":r.date,
             "sets":_json.loads(r.sets_json or "[]"),"duration":r.duration,
             "calories":r.calories,"notes":r.notes,
             "logged_at":r.logged_at.isoformat() if r.logged_at else None} for r in rows]

@app.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    row = db.query(WorkoutLog).filter(WorkoutLog.id == workout_id).first()
    if not row: raise HTTPException(404, "Workout not found")
    db.delete(row); db.commit()
    return {"message": "Workout deleted"}

# ── VITALS ───────────────────────────────
@app.post("/vitals/{user_id}", status_code=201)
def add_vital(user_id: int, data: VitalIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    v = VitalLog(
        user_id=user_id, heart_rate=data.heart_rate,
        bp_systolic=data.bp_systolic, bp_diastolic=data.bp_diastolic,
        blood_sugar=data.blood_sugar, sleep_hrs=data.sleep_hrs,
        steps=data.steps, spo2=data.spo2, weight=data.weight,
        temperature=data.temperature, notes=data.notes
    )
    db.add(v); db.commit(); db.refresh(v)
    alerts = check_alerts(v, user)
    if alerts:
        # Save health alerts
        for a in alerts:
            ha = HealthAlert(
                user_id=user_id, alert_type=a["type"],
                value=a["value"], severity=a["severity"], message=a["message"]
            )
            db.add(ha)
        db.commit()
        try:
            from email_service import send_health_alert
            for a in alerts:
                if a["severity"] == "critical":
                    send_health_alert(user.email, user.name, a["type"], a["message"], "Safe range")
        except: pass
    return {"id": v.id, "message": "Vitals saved", "alerts": [a["message"] for a in alerts]}

@app.get("/vitals/{user_id}")
def get_vitals(user_id: int, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.query(VitalLog).filter(VitalLog.user_id == user_id)\
             .order_by(VitalLog.recorded_at.desc()).limit(limit).all()
    return [{
        "id":r.id,"heart_rate":r.heart_rate,
        "bp":f"{r.bp_systolic}/{r.bp_diastolic}" if r.bp_systolic else None,
        "bp_systolic":r.bp_systolic,"bp_diastolic":r.bp_diastolic,
        "blood_sugar":r.blood_sugar,"sleep_hrs":r.sleep_hrs,"steps":r.steps,
        "spo2":r.spo2,"weight":r.weight,"temperature":r.temperature,
        "notes":r.notes,
        "recorded_at":r.recorded_at.isoformat() if r.recorded_at else None
    } for r in rows]

# ── PROGRESS ─────────────────────────────
@app.post("/progress/{user_id}", status_code=201)
def add_progress(user_id: int, data: ProgressIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    bmi = None
    if data.weight and user.height and user.height > 0:
        bmi = round(data.weight / ((user.height / 100) ** 2), 2)
    entry = ProgressLog(
        user_id=user_id, date=data.date, weight=data.weight, body_fat=data.body_fat,
        bmi=bmi, chest=data.chest, waist=data.waist, hips=data.hips,
        bicep=data.bicep, thigh=data.thigh, neck=data.neck, notes=data.notes
    )
    db.add(entry); db.commit(); db.refresh(entry)
    return {"id": entry.id, "message": "Progress logged", "bmi": bmi}

@app.get("/progress/{user_id}")
def get_progress(user_id: int, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.query(ProgressLog).filter(ProgressLog.user_id == user_id)\
             .order_by(ProgressLog.logged_at.desc()).limit(limit).all()
    return [{"id":r.id,"date":r.date,"weight":r.weight,"body_fat":r.body_fat,"bmi":r.bmi,
             "chest":r.chest,"waist":r.waist,"hips":r.hips,"bicep":r.bicep,
             "thigh":r.thigh,"neck":r.neck,"notes":r.notes,
             "logged_at":r.logged_at.isoformat() if r.logged_at else None} for r in rows]

@app.delete("/progress/{prog_id}")
def delete_progress(prog_id: int, db: Session = Depends(get_db)):
    row = db.query(ProgressLog).filter(ProgressLog.id == prog_id).first()
    if not row: raise HTTPException(404, "Progress entry not found")
    db.delete(row); db.commit()
    return {"message": "Deleted"}

# ── APPOINTMENTS ─────────────────────────
@app.post("/appointments/{user_id}", status_code=201)
def book_appointment(user_id: int, data: AppointmentIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    appt = Appointment(
        user_id=user_id, doctor_name=data.doctor_name, appt_date=data.appt_date,
        appt_time=data.appt_time, appt_type=data.appt_type,
        speciality=data.speciality, reason=data.reason
    )
    db.add(appt); db.commit(); db.refresh(appt)
    try:
        from email_service import send_appointment_confirmation
        send_appointment_confirmation(user.email, user.name, data.doctor_name,
                                      data.appt_date, data.appt_time or "", data.appt_type or "In-Clinic")
    except: pass
    return {"id": appt.id, "message": "Appointment booked", "status": "Pending"}

@app.get("/appointments/{user_id}")
def get_appointments(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(Appointment).filter(Appointment.user_id == user_id)\
             .order_by(Appointment.appt_date.desc()).all()
    return [{"id":r.id,"doctor":r.doctor_name,"date":r.appt_date,"time":r.appt_time,
             "type":r.appt_type,"status":r.status,"reason":r.reason,"speciality":r.speciality,
             "prescription":r.prescription} for r in rows]

@app.patch("/appointments/{appt_id}/status")
def update_appt(appt_id: int, body: dict = Body(...), db: Session = Depends(get_db)):
    status_val = body.get("status", "")
    valid_statuses = {"Pending", "Confirmed", "Done", "Cancelled"}
    if status_val not in valid_statuses:
        raise HTTPException(400, f"Status must be one of: {', '.join(valid_statuses)}")
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt: raise HTTPException(404, "Appointment not found")
    appt.status = status_val; db.commit()
    return {"message": f"Status updated to {status_val}"}

@app.delete("/appointments/{appt_id}")
def cancel_appointment(appt_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt: raise HTTPException(404, "Appointment not found")
    db.delete(appt); db.commit()
    return {"message": "Appointment cancelled"}

# ── FOOD LOGS ─────────────────────────────
@app.post("/food-logs/{user_id}", status_code=201)
def add_food(user_id: int, data: FoodLogIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    entry = FoodLog(
        user_id=user_id,
        log_date=data.log_date or datetime.utcnow().strftime('%Y-%m-%d'),
        meal_type=data.meal_type, food_name=data.food_name,
        calories=data.calories, protein_g=data.protein_g,
        carbs_g=data.carbs_g, fat_g=data.fat_g,
        fiber_g=data.fiber_g, quantity=data.quantity
    )
    db.add(entry); db.commit(); db.refresh(entry)
    return {"id": entry.id, "message": "Food logged"}

@app.get("/food-logs/{user_id}")
def get_food(user_id: int, log_date: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FoodLog).filter(FoodLog.user_id == user_id)
    if log_date: q = q.filter(FoodLog.log_date == log_date)
    rows = q.order_by(FoodLog.logged_at.desc()).limit(200).all()
    return [{"id":r.id,"date":r.log_date,"meal":r.meal_type,"food":r.food_name,
             "calories":r.calories,"protein":r.protein_g,"carbs":r.carbs_g,
             "fat":r.fat_g,"fiber":r.fiber_g,"quantity":r.quantity,
             "logged_at":r.logged_at.isoformat() if r.logged_at else None} for r in rows]

@app.delete("/food-logs/{log_id}")
def delete_food(log_id: int, db: Session = Depends(get_db)):
    row = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not row: raise HTTPException(404, "Food log not found")
    db.delete(row); db.commit()
    return {"message": "Deleted"}

# ── HEALTH ALERTS ────────────────────────
@app.get("/alerts/{user_id}")
def get_alerts(user_id: int, unacknowledged_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(HealthAlert).filter(HealthAlert.user_id == user_id)
    if unacknowledged_only: q = q.filter(HealthAlert.acknowledged == False)
    rows = q.order_by(HealthAlert.created_at.desc()).limit(50).all()
    return [{"id":r.id,"type":r.alert_type,"severity":r.severity,"message":r.message,
             "value":r.value,"acknowledged":r.acknowledged,
             "created_at":r.created_at.isoformat() if r.created_at else None} for r in rows]

@app.patch("/alerts/{alert_id}/acknowledge")
def ack_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(HealthAlert).filter(HealthAlert.id == alert_id).first()
    if not a: raise HTTPException(404, "Alert not found")
    a.acknowledged = True; db.commit()
    return {"message": "Acknowledged"}

# ── DOCTOR ───────────────────────────────
@app.get("/doctor/patients/{doctor_id}")
def get_patients(doctor_id: int, db: Session = Depends(get_db)):
    patients = db.query(User).filter(User.role == "member", User.is_active == True).all()
    result = []
    for p in patients:
        lv = db.query(VitalLog).filter(VitalLog.user_id == p.id)\
               .order_by(VitalLog.recorded_at.desc()).first()
        result.append({
            "id":p.id,"name":p.name,"age":p.age,"gender":p.gender,
            "email":p.email,"plan":p.plan,
            "condition":p.disease or "None","injury":p.injury or "None",
            "goal":p.goal,"level":p.level,
            "latest_vitals":{
                "hr":lv.heart_rate,
                "bp":f"{lv.bp_systolic}/{lv.bp_diastolic}" if lv and lv.bp_systolic else None,
                "sugar":lv.blood_sugar,"sleep":lv.sleep_hrs,
                "spo2":lv.spo2,"steps":lv.steps
            } if lv else None
        })
    return result

@app.post("/doctor/notes")
def add_note(body: dict = Body(...), db: Session = Depends(get_db)):
    doctor_id = body.get("doctor_id")
    patient_id = body.get("patient_id")
    note = body.get("note", "").strip()
    if not note: raise HTTPException(400, "Note content required")
    if not doctor_id or not patient_id: raise HTTPException(400, "Doctor and patient IDs required")
    n = DoctorNote(
        doctor_id=doctor_id, patient_id=patient_id, note=note,
        restrictions=body.get("restrictions"),
        approved_ex=body.get("approved_ex"),
        treatment_plan=body.get("treatment_plan"),
        next_review=body.get("next_review")
    )
    db.add(n); db.commit(); db.refresh(n)
    return {"id": n.id, "message": "Note saved"}

@app.get("/doctor/notes/{patient_id}")
def get_notes(patient_id: int, db: Session = Depends(get_db)):
    rows = db.query(DoctorNote).filter(DoctorNote.patient_id == patient_id, DoctorNote.is_active == True)\
             .order_by(DoctorNote.created_at.desc()).all()
    return [{"id":r.id,"note":r.note,"restrictions":r.restrictions,
             "approved_ex":r.approved_ex,"treatment_plan":r.treatment_plan,
             "next_review":r.next_review,
             "created_at":r.created_at.isoformat() if r.created_at else None} for r in rows]

@app.get("/doctor/appointments/{doctor_id}")
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    rows = db.query(Appointment).order_by(Appointment.appt_date).all()
    return [{"id":r.id,"user_id":r.user_id,"doctor":r.doctor_name,"date":r.appt_date,
             "time":r.appt_time,"type":r.appt_type,"status":r.status,
             "reason":r.reason,"speciality":r.speciality} for r in rows]

# ── REPORTS ──────────────────────────────
@app.get("/reports/{user_id}")
def get_report(user_id: int, db: Session = Depends(get_db)):
    week_ago = datetime.utcnow() - timedelta(days=7)
    wk_week = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user_id, WorkoutLog.logged_at >= week_ago
    ).all()
    lv = db.query(VitalLog).filter(VitalLog.user_id == user_id)\
           .order_by(VitalLog.recorded_at.desc()).first()
    lp = db.query(ProgressLog).filter(ProgressLog.user_id == user_id)\
           .order_by(ProgressLog.logged_at.desc()).first()
    # Score calculation
    score = min(100,
        len(wk_week) * 6
        + (15 if lv and lv.heart_rate and 60 <= lv.heart_rate <= 100 else 0)
        + (20 if lv and lv.sleep_hrs and lv.sleep_hrs >= 7 else 0)
        + (20 if lv and lv.steps and lv.steps >= 8000 else 0)
        + (15 if lv and lv.blood_sugar and 70 <= lv.blood_sugar <= 100 else 0)
    )
    # Muscle breakdown for workouts this week
    muscle_groups = {}
    for w in wk_week:
        mg = w.muscle or "Other"
        muscle_groups[mg] = muscle_groups.get(mg, 0) + 1

    return {
        "wellness_score": score,
        "workouts_this_week": len(wk_week),
        "total_calories": sum(w.calories or 0 for w in wk_week),
        "total_duration": sum(w.duration or 0 for w in wk_week),
        "muscle_breakdown": muscle_groups,
        "latest_vitals": {
            "heart_rate": lv.heart_rate if lv else None,
            "blood_pressure": f"{lv.bp_systolic}/{lv.bp_diastolic}" if lv and lv.bp_systolic else None,
            "blood_sugar": lv.blood_sugar if lv else None,
            "sleep_hrs": lv.sleep_hrs if lv else None,
            "steps": lv.steps if lv else None,
            "spo2": lv.spo2 if lv else None,
            "weight": lv.weight if lv else None,
            "temperature": lv.temperature if lv else None,
        } if lv else None,
        "current_weight": lp.weight if lp else None,
        "current_bmi": lp.bmi if lp else None,
        "current_body_fat": lp.body_fat if lp else None,
    }

# ── AI PROXY ─────────────────────────────
@app.post("/ai/chat")
async def ai_chat(data: AIChatIn):
    import httpx
    key = load_settings().get("anthropic_api_key") or ANTHROPIC_KEY
    if not key:
        raise HTTPException(503, "AI service not configured. Set ANTHROPIC_API_KEY in .env or Admin Settings.")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":min(data.max_tokens, 2000),
                      "messages":[{"role":"user","content":data.prompt}]}
            )
        if r.status_code != 200:
            raise HTTPException(502, f"AI error: {r.text[:300]}")
        resp_data = r.json()
        text = resp_data.get("content", [{}])[0].get("text", "")
        return {"text": text}
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"AI service error: {str(e)[:200]}")

# ── PLAN GENERATOR (C++) ──────────────────
@app.post("/generate-plan")
def generate_plan(data: PlanGenerateIn):
    bmi = round(data.weight / ((data.height / 100) ** 2), 1)
    prot = round(data.weight * (2.2 if data.goal == "Muscle Gain" else 1.8 if data.goal == "Strength" else 1.6))
    exe = os.path.join(os.path.dirname(__file__), "workout.exe")
    if os.path.exists(exe):
        try:
            r = subprocess.run(
                [exe],
                input=f"{data.age}\n{data.weight}\n{data.height}\n{data.injury}\n{data.disease}\n{data.goal}\n{data.location}\n",
                text=True, capture_output=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                return {"plan": r.stdout}
        except: pass
    # Fallback plan
    plan_text = f"""BMI: {bmi} ({_bmi_cat(bmi)}) | Goal: {data.goal} | Location: {data.location}

📊 Nutritional Targets:
• Protein: {prot}g/day
• Calories: {_calc_calories(data.weight, data.height, data.age, data.goal)} kcal/day
• Water: {round(data.weight * 0.033, 1)}L/day

🏋️ Weekly Schedule (4-5 days):
• Day 1: Push (Chest, Shoulders, Triceps)
• Day 2: Pull (Back, Biceps)
• Day 3: Legs & Core
• Day 4: Rest or Active Recovery
• Day 5: Full Body / Sport
• Day 6-7: Rest

⚕️ Health Notes:
• Injury consideration: {data.injury}
• Health condition: {data.disease}

📈 Progressive Overload: Increase weight/reps by 5-10% every 2 weeks."""
    return {"plan": plan_text}

def _bmi_cat(bmi: float) -> str:
    if bmi < 18.5: return "Underweight"
    elif bmi < 25: return "Normal"
    elif bmi < 30: return "Overweight"
    return "Obese"

def _calc_calories(weight, height, age, goal):
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    tdee = bmr * 1.55
    if goal == "Weight Loss": return round(tdee * 0.8)
    elif goal in ("Muscle Gain", "Strength"): return round(tdee * 1.15)
    return round(tdee)

# ── ADMIN: PLANS ─────────────────────────
@app.get("/admin/plans")
def get_plans():
    return load_plans()

@app.post("/admin/plans/{plan_id}")
def upsert_plan(plan_id: str, data: PlanModel):
    plans = load_plans()
    idx = next((i for i,p in enumerate(plans) if p["id"] == plan_id), None)
    d = data.model_dump()
    if idx is not None: plans[idx] = d
    else: plans.append(d)
    save_plans(plans)
    return {"message": f"Plan '{plan_id}' saved"}

@app.delete("/admin/plans/{plan_id}")
def delete_plan(plan_id: str):
    plans = [p for p in load_plans() if p["id"] != plan_id]
    save_plans(plans)
    return {"message": "Plan deleted"}

# ── ADMIN: SETTINGS ───────────────────────
@app.get("/admin/settings")
def get_settings():
    s = load_settings()
    # Mask sensitive values
    return {k: ("***" if v and any(x in k.lower() for x in ["key","password","secret","token"]) else v)
            for k,v in s.items()}

@app.post("/admin/settings")
def save_setting(data: SettingIn):
    s = load_settings(); s[data.key] = data.value; save_settings(s)
    return {"message": f"Setting '{data.key}' saved"}

@app.post("/admin/settings/bulk")
def save_settings_bulk(data: dict = Body(...)):
    if not isinstance(data, dict):
        raise HTTPException(400, "Expected JSON object")
    s = load_settings(); s.update(data); save_settings(s)
    return {"message": f"{len(data)} settings saved"}

# ── ADMIN: MEMBERS ────────────────────────
@app.get("/admin/members")
def admin_members(role: Optional[str] = None, plan: Optional[str] = None,
                  db: Session = Depends(get_db)):
    q = db.query(User)
    if role: q = q.filter(User.role == role)
    if plan: q = q.filter(User.plan == plan)
    users = q.order_by(User.joined_at.desc()).all()
    return [{"id":u.id,"name":u.name,"email":u.email,"role":u.role,"plan":u.plan,
             "goal":u.goal,"weight":u.weight,"height":u.height,"is_active":u.is_active,
             "age":u.age,"gender":u.gender,"level":u.level,
             "joined_at":u.joined_at.isoformat() if u.joined_at else None,
             "last_login":u.last_login.isoformat() if u.last_login else None} for u in users]

@app.patch("/admin/members/{uid}")
def admin_update_member(uid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == uid).first()
    if not user: raise HTTPException(404, "User not found")
    allowed = {"plan","role","is_active","goal","injury","disease","level"}
    for k,v in data.items():
        if k in allowed:
            if k == "role" and v not in VALID_ROLES:
                continue
            setattr(user, k, v)
    db.commit()
    return {"message": "Member updated"}

@app.delete("/admin/members/{uid}")
def admin_delete_member(uid: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == uid).first()
    if not user: raise HTTPException(404, "User not found")
    db.delete(user); db.commit()
    return {"message": "Member deleted"}

@app.get("/admin/analytics")
def admin_analytics(db: Session = Depends(get_db)):
    members = db.query(User).filter(User.role == "member", User.is_active == True).all()
    all_users = db.query(User).all()
    plans = load_plans()
    prices = {p["name"]: p["price"] for p in plans}
    revenue = sum(prices.get(m.plan, 0) for m in members)
    plan_dist = {}; goal_dist = {}; level_dist = {}
    for m in members:
        plan_dist[m.plan] = plan_dist.get(m.plan, 0) + 1
        if m.goal: goal_dist[m.goal] = goal_dist.get(m.goal, 0) + 1
        if m.level: level_dist[m.level] = level_dist.get(m.level, 0) + 1
    role_dist = {}
    for u in all_users:
        role_dist[u.role] = role_dist.get(u.role, 0) + 1
    return {
        "total_members": len(members),
        "total_users": len(all_users),
        "monthly_revenue_pkr": revenue,
        "total_workouts": db.query(WorkoutLog).count(),
        "total_vitals": db.query(VitalLog).count(),
        "total_appointments": db.query(Appointment).count(),
        "total_food_logs": db.query(FoodLog).count(),
        "plan_distribution": plan_dist,
        "goal_distribution": goal_dist,
        "level_distribution": level_dist,
        "role_distribution": role_dist
    }

# ── PROMO CODES ───────────────────────────
@app.get("/admin/promos")
def get_promos(): return load_promos()

@app.post("/admin/promos")
def add_promo(data: dict = Body(...)):
    code = data.get("code", "").strip().upper()
    if not code: raise HTTPException(400, "Promo code required")
    p = load_promos()
    if any(x["code"] == code for x in p):
        raise HTTPException(400, "Promo code already exists")
    data["code"] = code
    p.append(data); save_promos(p)
    return {"message": "Promo code created"}

@app.patch("/admin/promos/{code}/toggle")
def toggle_promo(code: str):
    p = load_promos()
    for x in p:
        if x["code"] == code.upper():
            x["active"] = not x.get("active", True); break
    save_promos(p); return {"message": "Toggled"}

@app.post("/promos/{code}/validate")
def validate_promo(code: str, body: dict = Body(default={})):
    plan = body.get("plan", "")
    p = next((x for x in load_promos() if x["code"] == code.upper() and x.get("active")), None)
    if not p: raise HTTPException(404, "Invalid or expired promo code")
    return {"valid": True, "discount": p.get("disc", "0%"), "code": p["code"], "plan": p.get("plan", "")}

# Also keep old route for backward compatibility
@app.post("/admin/promos/{code}/validate")
def validate_promo_admin(code: str, plan: str = ""):
    p = next((x for x in load_promos() if x["code"] == code.upper() and x.get("active")), None)
    if not p: raise HTTPException(404, "Invalid or expired promo code")
    return {"valid": True, "discount": p.get("disc", "0%"), "code": p["code"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
