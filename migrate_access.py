"""
══════════════════════════════════════════════════════════════
  FITMART — Access Database Migration Script
  Migrates Fit_Mart_Data_Base.accdb → SQLite/PostgreSQL

  Requirements:
    pip install pyodbc pandas sqlalchemy --break-system-packages

  Usage:
    1. Export each Access table to CSV (External Data → Export → CSV)
    2. Place CSVs in the migration/ folder
    3. Run: python migrate_access.py

  Or for direct Access connection (Windows + Access driver only):
    python migrate_access.py --direct
══════════════════════════════════════════════════════════════
"""

import os, sys, csv, json, hashlib, argparse
from datetime import datetime
from pathlib import Path

# SQLAlchemy + our models
from sqlalchemy.orm import Session
from main import (
    engine, SessionLocal, Base,
    User, WorkoutLog, VitalLog, ProgressLog, Appointment,
    hash_password
)

Base.metadata.create_all(bind=engine)

MIGRATION_DIR = Path(__file__).parent / "migration"
MIGRATION_DIR.mkdir(exist_ok=True)

DEFAULT_PASSWORD = "FitMart2025!"   # All migrated users get this password (must change)


# ══════════════════════════════════════════
#  CSV MIGRATION (cross-platform)
# ══════════════════════════════════════════

def migrate_users_csv(db: Session, filepath: str):
    """
    Expected CSV columns (adjust mapping below to match your Access table):
    UserID, FullName, Email, Password, Role, Age, Gender, Weight, Height,
    Injury, Disease, Goal, Plan, JoinedAt
    """
    print(f"\n📥 Migrating users from {filepath}...")
    count = 0
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', row.get('email', '')).strip()
            if not email:
                continue
            if db.query(User).filter(User.email == email).first():
                print(f"  ⚠ Skipping duplicate: {email}")
                continue
            user = User(
                name    = row.get('FullName', row.get('Name', email.split('@')[0])).strip(),
                email   = email,
                password= hash_password(row.get('Password', DEFAULT_PASSWORD).strip() or DEFAULT_PASSWORD),
                role    = (row.get('Role', 'member') or 'member').lower().strip(),
                age     = _int(row.get('Age')),
                gender  = row.get('Gender', '').strip() or None,
                weight  = _float(row.get('Weight')),
                height  = _float(row.get('Height')),
                injury  = row.get('Injury', 'None').strip() or 'None',
                disease = row.get('Disease', row.get('Condition', 'None')).strip() or 'None',
                goal    = row.get('Goal', 'General Fitness').strip() or 'General Fitness',
                plan    = row.get('Plan', row.get('Membership', 'Basic')).strip() or 'Basic',
                joined_at = _date(row.get('JoinedAt', row.get('JoinDate', ''))) or datetime.utcnow(),
            )
            db.add(user)
            count += 1
            if count % 50 == 0:
                db.commit()
    db.commit()
    print(f"  ✅ Migrated {count} users")
    return count


def migrate_vitals_csv(db: Session, filepath: str):
    """
    Expected columns: UserEmail (or UserID), HeartRate, BPSystolic, BPDiastolic,
    BloodSugar, SleepHrs, Steps, SpO2, RecordedAt
    """
    print(f"\n📥 Migrating vitals from {filepath}...")
    count = 0
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = _find_user(db, row)
            if not user:
                continue
            vital = VitalLog(
                user_id     = user.id,
                heart_rate  = _float(row.get('HeartRate', row.get('HR'))),
                bp_systolic = _float(row.get('BPSystolic', row.get('Systolic'))),
                bp_diastolic= _float(row.get('BPDiastolic', row.get('Diastolic'))),
                blood_sugar = _float(row.get('BloodSugar', row.get('Sugar'))),
                sleep_hrs   = _float(row.get('SleepHrs', row.get('Sleep'))),
                steps       = _int(row.get('Steps')),
                spo2        = _float(row.get('SpO2', row.get('Oxygen'))),
                recorded_at = _date(row.get('RecordedAt', row.get('Date'))) or datetime.utcnow(),
            )
            db.add(vital)
            count += 1
            if count % 100 == 0:
                db.commit()
    db.commit()
    print(f"  ✅ Migrated {count} vital records")
    return count


def migrate_workouts_csv(db: Session, filepath: str):
    """
    Expected columns: UserEmail, Exercise, Muscle, Date, Sets, Reps,
    Weight, Duration, Calories, Notes
    """
    print(f"\n📥 Migrating workouts from {filepath}...")
    count = 0
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = _find_user(db, row)
            if not user:
                continue
            sets = _int(row.get('Sets', 3))
            reps = _int(row.get('Reps', 10))
            weight = _float(row.get('Weight', row.get('WeightKg', 0)))
            sets_json = json.dumps([{"set": i+1, "reps": reps, "weight": weight, "rpe": 7} for i in range(sets)])
            wl = WorkoutLog(
                user_id  = user.id,
                exercise = row.get('Exercise', 'Unknown').strip(),
                muscle   = row.get('Muscle', row.get('MuscleGroup', 'Other')).strip(),
                date     = row.get('Date', datetime.utcnow().strftime('%Y-%m-%d')).strip()[:10],
                sets_json= sets_json,
                duration = _int(row.get('Duration', row.get('DurationMin'))),
                calories = _int(row.get('Calories', row.get('CaloriesBurned'))),
                notes    = row.get('Notes', '').strip() or None,
            )
            db.add(wl)
            count += 1
            if count % 100 == 0:
                db.commit()
    db.commit()
    print(f"  ✅ Migrated {count} workout logs")
    return count


def migrate_progress_csv(db: Session, filepath: str):
    """
    Expected columns: UserEmail, Date, Weight, BodyFat, Chest, Waist, Hips, Bicep
    """
    print(f"\n📥 Migrating progress from {filepath}...")
    count = 0
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = _find_user(db, row)
            if not user:
                continue
            pl = ProgressLog(
                user_id  = user.id,
                date     = row.get('Date', datetime.utcnow().strftime('%Y-%m-%d')).strip()[:10],
                weight   = _float(row.get('Weight', row.get('WeightKg'))),
                body_fat = _float(row.get('BodyFat', row.get('BodyFatPct'))),
                chest    = _float(row.get('Chest')),
                waist    = _float(row.get('Waist')),
                hips     = _float(row.get('Hips')),
                bicep    = _float(row.get('Bicep', row.get('Arm'))),
            )
            db.add(pl)
            count += 1
            if count % 100 == 0:
                db.commit()
    db.commit()
    print(f"  ✅ Migrated {count} progress entries")
    return count


def migrate_appointments_csv(db: Session, filepath: str):
    """
    Expected columns: UserEmail, DoctorName, AppointmentDate, Type, Reason, Status
    """
    print(f"\n📥 Migrating appointments from {filepath}...")
    count = 0
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = _find_user(db, row)
            if not user:
                continue
            appt = Appointment(
                user_id    = user.id,
                doctor_name= row.get('DoctorName', row.get('Doctor', 'Dr. TBD')).strip(),
                appt_date  = row.get('AppointmentDate', row.get('Date', '')).strip()[:10],
                appt_type  = row.get('Type', 'In-Clinic').strip(),
                reason     = row.get('Reason', '').strip() or None,
                status     = row.get('Status', 'Done').strip(),
            )
            db.add(appt)
            count += 1
    db.commit()
    print(f"  ✅ Migrated {count} appointments")
    return count


# ══════════════════════════════════════════
#  DIRECT ACCESS CONNECTION (Windows only)
# ══════════════════════════════════════════

def migrate_direct_access(accdb_path: str):
    """
    Direct migration from Access file (requires Windows + Microsoft Access Driver)
    Install driver: https://www.microsoft.com/en-us/download/details.aspx?id=54920
    """
    try:
        import pyodbc
    except ImportError:
        print("❌ pyodbc not installed. Run: pip install pyodbc")
        sys.exit(1)

    conn_str = (
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"Dbq={accdb_path};"
    )
    try:
        conn = pyodbc.connect(conn_str)
        print(f"✅ Connected to {accdb_path}")
    except Exception as e:
        print(f"❌ Could not connect to Access database: {e}")
        print("   Make sure you have the Access ODBC driver installed.")
        sys.exit(1)

    cursor = conn.cursor()
    db = SessionLocal()

    # List all tables
    tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
    print(f"\n📊 Found tables: {tables}")

    # Export each table to CSV for review
    for table in tables:
        cursor.execute(f"SELECT * FROM [{table}]")
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        csv_path = MIGRATION_DIR / f"{table}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)
        print(f"  📄 Exported {table} → {csv_path} ({len(rows)} rows)")

    conn.close()
    db.close()
    print("\n✅ Access tables exported to migration/ folder.")
    print("   Review the CSVs, adjust column mapping in this script, then run without --direct")


# ══════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════

def _int(v):
    try: return int(str(v).strip()) if v and str(v).strip() not in ('', 'None', 'N/A') else None
    except: return None

def _float(v):
    try: return float(str(v).strip()) if v and str(v).strip() not in ('', 'None', 'N/A') else None
    except: return None

def _date(v):
    if not v or str(v).strip() in ('', 'None', 'N/A'):
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try: return datetime.strptime(str(v).strip()[:10], fmt)
        except: pass
    return None

def _find_user(db: Session, row: dict):
    """Find user by email or name."""
    email = row.get('UserEmail', row.get('Email', '')).strip()
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user: return user
    name = row.get('UserName', row.get('Name', '')).strip()
    if name:
        user = db.query(User).filter(User.name.ilike(f'%{name}%')).first()
        if user: return user
    user_id = _int(row.get('UserID', row.get('user_id')))
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None


# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════

def run_csv_migration():
    db = SessionLocal()
    total = 0
    csv_map = {
        'users.csv':        migrate_users_csv,
        'vitals.csv':       migrate_vitals_csv,
        'workouts.csv':     migrate_workouts_csv,
        'progress.csv':     migrate_progress_csv,
        'appointments.csv': migrate_appointments_csv,
    }
    found = False
    for filename, fn in csv_map.items():
        path = MIGRATION_DIR / filename
        if path.exists():
            found = True
            total += fn(db, str(path))
        else:
            print(f"  ⚠ {filename} not found in migration/ — skipping")
    db.close()
    if not found:
        print("\n⚠  No CSV files found in migration/ folder.")
        print("   Export your Access tables as CSV and place them in:")
        print(f"   {MIGRATION_DIR.resolve()}/")
        print("\n   Expected filenames: users.csv, vitals.csv, workouts.csv, progress.csv, appointments.csv")
    else:
        print(f"\n🎉 Migration complete! {total} total records imported.")
        print(f"   Default password for imported users: {DEFAULT_PASSWORD}")
        print("   Notify users to change their password on first login.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FitMart Access DB Migration')
    parser.add_argument('--direct', action='store_true', help='Connect directly to .accdb file')
    parser.add_argument('--accdb', default='../Fit_Mart_Data_Base.accdb', help='Path to .accdb file')
    args = parser.parse_args()

    print("══════════════════════════════════════════")
    print("  FitMart Database Migration Tool")
    print("══════════════════════════════════════════")

    if args.direct:
        migrate_direct_access(args.accdb)
    else:
        run_csv_migration()
