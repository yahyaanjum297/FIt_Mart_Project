-- ══════════════════════════════════════════════════════════════
--   FITMART — Production Database Schema v3.1
--   Compatible with: PostgreSQL 14+ / MySQL 8+ / SQLite 3.35+
--   Run (PostgreSQL): psql -U fitmart_user -d fitmart -f schema.sql
--   For SQLite: The Python backend auto-creates tables via SQLAlchemy
-- ══════════════════════════════════════════════════════════════

-- ─── ENABLE EXTENSIONS (PostgreSQL only) ──────────────────────
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── USERS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120)    NOT NULL CHECK (LENGTH(TRIM(name)) >= 2),
    email           VARCHAR(200)    NOT NULL UNIQUE CHECK (email ~* '^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'),
    password        VARCHAR(256)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'member'
                    CHECK (role IN ('member','doctor','trainer','admin')),
    age             INTEGER         CHECK (age IS NULL OR (age >= 10 AND age <= 110)),
    gender          VARCHAR(30)     CHECK (gender IS NULL OR gender IN ('Male','Female','Other','Prefer not to say')),
    weight          DECIMAL(5,2)    CHECK (weight IS NULL OR (weight >= 20 AND weight <= 500)),
    height          DECIMAL(5,2)    CHECK (height IS NULL OR (height >= 50 AND height <= 300)),
    injury          VARCHAR(255)    DEFAULT 'None',
    disease         VARCHAR(255)    DEFAULT 'None',
    allergies       VARCHAR(255),
    goal            VARCHAR(50)     DEFAULT 'General Fitness'
                    CHECK (goal IN ('Weight Loss','Muscle Gain','Endurance','Strength','Flexibility','General Fitness')),
    location        VARCHAR(20)     DEFAULT 'Gym'
                    CHECK (location IN ('Gym','Home')),
    level           VARCHAR(20)     DEFAULT 'Beginner'
                    CHECK (level IN ('Beginner','Intermediate','Advanced')),
    plan            VARCHAR(50)     DEFAULT 'Basic',
    is_active       BOOLEAN         DEFAULT TRUE,
    joined_at       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    last_login      TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role      ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_plan      ON users(plan);

-- ─── WORKOUT LOGS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workout_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise    VARCHAR(100)    NOT NULL CHECK (LENGTH(TRIM(exercise)) > 0),
    muscle      VARCHAR(50)     DEFAULT 'Other',
    date        DATE            NOT NULL,
    sets_json   TEXT            NOT NULL DEFAULT '[]',
    duration    INTEGER         CHECK (duration IS NULL OR (duration >= 0 AND duration <= 600)),
    calories    INTEGER         CHECK (calories IS NULL OR (calories >= 0 AND calories <= 5000)),
    notes       TEXT,
    logged_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wl_user_id   ON workout_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_wl_date      ON workout_logs(date);
CREATE INDEX IF NOT EXISTS idx_wl_logged_at ON workout_logs(logged_at);

-- ─── VITAL LOGS ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vital_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    heart_rate      DECIMAL(5,1)    CHECK (heart_rate IS NULL OR (heart_rate >= 20 AND heart_rate <= 300)),
    bp_systolic     DECIMAL(5,1)    CHECK (bp_systolic IS NULL OR (bp_systolic >= 50 AND bp_systolic <= 300)),
    bp_diastolic    DECIMAL(5,1)    CHECK (bp_diastolic IS NULL OR (bp_diastolic >= 30 AND bp_diastolic <= 200)),
    blood_sugar     DECIMAL(6,1)    CHECK (blood_sugar IS NULL OR (blood_sugar >= 20 AND blood_sugar <= 600)),
    sleep_hrs       DECIMAL(4,2)    CHECK (sleep_hrs IS NULL OR (sleep_hrs >= 0 AND sleep_hrs <= 24)),
    steps           INTEGER         CHECK (steps IS NULL OR (steps >= 0 AND steps <= 100000)),
    spo2            DECIMAL(5,2)    CHECK (spo2 IS NULL OR (spo2 >= 50 AND spo2 <= 100)),
    weight          DECIMAL(5,2)    CHECK (weight IS NULL OR (weight >= 20 AND weight <= 500)),
    temperature     DECIMAL(4,1)    CHECK (temperature IS NULL OR (temperature >= 30 AND temperature <= 45)),
    notes           TEXT,
    alert_sent      BOOLEAN         DEFAULT FALSE,
    recorded_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vl_user_id     ON vital_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_vl_recorded_at ON vital_logs(recorded_at);

-- ─── PROGRESS LOGS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS progress_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        DATE            NOT NULL,
    weight      DECIMAL(5,2)    CHECK (weight IS NULL OR (weight >= 20 AND weight <= 500)),
    body_fat    DECIMAL(5,2)    CHECK (body_fat IS NULL OR (body_fat >= 0 AND body_fat <= 70)),
    bmi         DECIMAL(5,2),
    chest       DECIMAL(5,1)    CHECK (chest IS NULL OR (chest >= 30 AND chest <= 200)),
    waist       DECIMAL(5,1)    CHECK (waist IS NULL OR (waist >= 30 AND waist <= 200)),
    hips        DECIMAL(5,1)    CHECK (hips IS NULL OR (hips >= 30 AND hips <= 200)),
    bicep       DECIMAL(5,1)    CHECK (bicep IS NULL OR (bicep >= 10 AND bicep <= 100)),
    thigh       DECIMAL(5,1)    CHECK (thigh IS NULL OR (thigh >= 20 AND thigh <= 150)),
    neck        DECIMAL(5,1)    CHECK (neck IS NULL OR (neck >= 20 AND neck <= 80)),
    notes       TEXT,
    logged_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pl_user_id ON progress_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_pl_date    ON progress_logs(date);

-- Auto-calculate BMI on insert/update (PostgreSQL)
CREATE OR REPLACE FUNCTION calc_bmi()
RETURNS TRIGGER AS $$
DECLARE v_height DECIMAL;
BEGIN
    SELECT height INTO v_height FROM users WHERE id = NEW.user_id;
    IF v_height IS NOT NULL AND v_height > 0 AND NEW.weight IS NOT NULL THEN
        NEW.bmi := ROUND(NEW.weight / POWER(v_height / 100.0, 2), 2);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_calc_bmi ON progress_logs;
CREATE TRIGGER trg_calc_bmi
BEFORE INSERT OR UPDATE ON progress_logs
FOR EACH ROW EXECUTE FUNCTION calc_bmi();

-- ─── APPOINTMENTS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doctor_id       INTEGER         REFERENCES users(id) ON DELETE SET NULL,
    doctor_name     VARCHAR(120)    NOT NULL CHECK (LENGTH(TRIM(doctor_name)) > 0),
    appt_date       DATE            NOT NULL,
    appt_time       TIME,
    appt_type       VARCHAR(20)     DEFAULT 'In-Clinic'
                    CHECK (appt_type IN ('In-Clinic','Video','Phone')),
    speciality      VARCHAR(60),
    reason          TEXT,
    status          VARCHAR(20)     DEFAULT 'Pending'
                    CHECK (status IN ('Pending','Confirmed','Done','Cancelled')),
    prescription    TEXT,
    follow_up_date  DATE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appt_user_id   ON appointments(user_id);
CREATE INDEX IF NOT EXISTS idx_appt_doctor_id ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appt_date      ON appointments(appt_date);
CREATE INDEX IF NOT EXISTS idx_appt_status    ON appointments(status);

-- Auto-update updated_at (PostgreSQL)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_appt_updated ON appointments;
CREATE TRIGGER trg_appt_updated
BEFORE UPDATE ON appointments
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── DOCTOR NOTES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctor_notes (
    id              SERIAL PRIMARY KEY,
    doctor_id       INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id      INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note            TEXT            NOT NULL CHECK (LENGTH(TRIM(note)) > 0),
    restrictions    TEXT,
    approved_ex     TEXT,
    treatment_plan  TEXT,
    next_review     DATE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dn_patient_id ON doctor_notes(patient_id);
CREATE INDEX IF NOT EXISTS idx_dn_doctor_id  ON doctor_notes(doctor_id);
CREATE INDEX IF NOT EXISTS idx_dn_is_active  ON doctor_notes(is_active);

-- ─── HEALTH ALERTS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_alerts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type      VARCHAR(50)     CHECK (alert_type IN ('heart_rate','blood_pressure','blood_sugar','spo2','temperature')),
    value           DECIMAL(8,2),
    threshold       DECIMAL(8,2),
    severity        VARCHAR(10)     DEFAULT 'warning'
                    CHECK (severity IN ('warning','critical')),
    message         TEXT            NOT NULL,
    acknowledged    BOOLEAN         DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ha_user_id    ON health_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_ha_severity   ON health_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_ha_ack        ON health_alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_ha_created_at ON health_alerts(created_at);

-- ─── FOOD LOGS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS food_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date        DATE            NOT NULL DEFAULT CURRENT_DATE,
    meal_type       VARCHAR(30)     CHECK (meal_type IS NULL OR meal_type IN ('Breakfast','Lunch','Dinner','Snack','Pre-Workout','Post-Workout')),
    food_name       VARCHAR(150)    NOT NULL CHECK (LENGTH(TRIM(food_name)) > 0),
    calories        INTEGER         CHECK (calories IS NULL OR (calories >= 0 AND calories <= 10000)),
    protein_g       DECIMAL(6,2)    CHECK (protein_g IS NULL OR (protein_g >= 0 AND protein_g <= 999)),
    carbs_g         DECIMAL(6,2)    CHECK (carbs_g IS NULL OR (carbs_g >= 0 AND carbs_g <= 999)),
    fat_g           DECIMAL(6,2)    CHECK (fat_g IS NULL OR (fat_g >= 0 AND fat_g <= 999)),
    fiber_g         DECIMAL(6,2)    CHECK (fiber_g IS NULL OR (fiber_g >= 0 AND fiber_g <= 999)),
    quantity        VARCHAR(50),
    logged_at       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fl_user_id  ON food_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_fl_log_date ON food_logs(log_date);
CREATE INDEX IF NOT EXISTS idx_fl_meal     ON food_logs(meal_type);

-- ─── MEMBERSHIPS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS memberships (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan            VARCHAR(50)     NOT NULL DEFAULT 'Basic',
    billing_cycle   VARCHAR(10)     DEFAULT 'monthly'
                    CHECK (billing_cycle IN ('monthly','annual')),
    amount_pkr      INTEGER         CHECK (amount_pkr IS NULL OR amount_pkr >= 0),
    start_date      DATE            NOT NULL DEFAULT CURRENT_DATE,
    end_date        DATE,
    auto_renew      BOOLEAN         DEFAULT TRUE,
    is_active       BOOLEAN         DEFAULT TRUE,
    payment_method  VARCHAR(30),
    transaction_id  VARCHAR(100)    UNIQUE,
    promo_code      VARCHAR(50),
    discount_pct    INTEGER         DEFAULT 0,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mem_user_id   ON memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_mem_is_active ON memberships(is_active);

-- ─── CLASS BOOKINGS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS class_bookings (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    class_name      VARCHAR(100)    NOT NULL,
    trainer_name    VARCHAR(100),
    class_date      DATE            NOT NULL,
    class_time      TIME            NOT NULL,
    status          VARCHAR(20)     DEFAULT 'Confirmed'
                    CHECK (status IN ('Confirmed','Cancelled','Attended','No-Show')),
    notes           TEXT,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cb_user_id    ON class_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_cb_class_date ON class_bookings(class_date);

-- ─── PASSWORD RESET TOKENS ───────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      VARCHAR(100)    NOT NULL UNIQUE,
    expires_at TIMESTAMP       NOT NULL,
    used       BOOLEAN         DEFAULT FALSE,
    created_at TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prt_token   ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_prt_user_id ON password_reset_tokens(user_id);

-- ══════════════════════════════════════════
--   VIEWS
-- ══════════════════════════════════════════

-- Latest vitals per user
CREATE OR REPLACE VIEW v_latest_vitals AS
SELECT DISTINCT ON (user_id)
    user_id, heart_rate, bp_systolic, bp_diastolic,
    blood_sugar, sleep_hrs, steps, spo2, weight,
    temperature, recorded_at
FROM vital_logs
ORDER BY user_id, recorded_at DESC;

-- Weekly workout summary per user
CREATE OR REPLACE VIEW v_weekly_workouts AS
SELECT
    user_id,
    COUNT(*) AS sessions,
    COALESCE(SUM(calories), 0) AS total_calories,
    COALESCE(SUM(duration), 0) AS total_minutes,
    MAX(date) AS last_session
FROM workout_logs
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY user_id;

-- Wellness score per user (0–100)
CREATE OR REPLACE VIEW v_wellness_score AS
SELECT
    u.id AS user_id,
    u.name,
    u.email,
    u.plan,
    LEAST(100,
        COALESCE(ww.sessions, 0) * 6
        + CASE WHEN lv.heart_rate BETWEEN 60 AND 100 THEN 15 ELSE 0 END
        + CASE WHEN lv.sleep_hrs >= 7               THEN 20 ELSE 0 END
        + CASE WHEN lv.steps >= 8000                THEN 20 ELSE 0 END
        + CASE WHEN lv.blood_sugar BETWEEN 70 AND 100 THEN 15 ELSE 0 END
    ) AS wellness_score
FROM users u
LEFT JOIN v_latest_vitals  lv ON lv.user_id = u.id
LEFT JOIN v_weekly_workouts ww ON ww.user_id = u.id
WHERE u.role = 'member' AND u.is_active = TRUE;

-- ══════════════════════════════════════════
--   SEED DATA (with SHA-256 hashed passwords)
--   password for all: FitMart2025!
--   Hash: sha256("FitMart2025!" + "fitmart_salt_2025_v2")
-- ══════════════════════════════════════════
INSERT INTO users (name, email, password, role, age, gender, weight, height, goal, plan, is_active) VALUES
  ('Admin',        'admin@fitmart.pk',   '5e92b2b1ffc74a6e3a7f06dab9f6e7b25b2ad1c75ee1d00c57f8e1e71f3d7fb3', 'admin',   30, 'Male',   70,  175, 'General Fitness', 'Elite',  TRUE),
  ('Dr. Fatima',   'doctor@fitmart.pk',  '5e92b2b1ffc74a6e3a7f06dab9f6e7b25b2ad1c75ee1d00c57f8e1e71f3d7fb3', 'doctor',  38, 'Female', 58,  162, 'General Fitness', 'Elite',  TRUE),
  ('Ali Raza',     'ali@fitmart.pk',     '5e92b2b1ffc74a6e3a7f06dab9f6e7b25b2ad1c75ee1d00c57f8e1e71f3d7fb3', 'member',  28, 'Male',   78,  178, 'Weight Loss',     'Pro',    TRUE),
  ('Sara Ahmed',   'sara@fitmart.pk',    '5e92b2b1ffc74a6e3a7f06dab9f6e7b25b2ad1c75ee1d00c57f8e1e71f3d7fb3', 'member',  34, 'Female', 65,  163, 'Muscle Gain',     'Basic',  TRUE),
  ('Umar Khan',    'umar@fitmart.pk',    '5e92b2b1ffc74a6e3a7f06dab9f6e7b25b2ad1c75ee1d00c57f8e1e71f3d7fb3', 'trainer', 32, 'Male',   82,  183, 'General Fitness', 'Elite',  TRUE)
ON CONFLICT (email) DO NOTHING;

-- ══════════════════════════════════════════
--   USEFUL QUERIES
-- ══════════════════════════════════════════

-- Full patient dashboard for doctor:
-- SELECT u.name, u.age, u.gender, u.disease, u.injury, u.goal,
--        lv.heart_rate, lv.blood_sugar, lv.spo2, ws.wellness_score
-- FROM users u
-- LEFT JOIN v_latest_vitals lv  ON lv.user_id = u.id
-- LEFT JOIN v_wellness_score ws ON ws.user_id = u.id
-- WHERE u.role = 'member' AND u.is_active = TRUE
-- ORDER BY ws.wellness_score ASC;

-- This week's workouts for user:
-- SELECT exercise, muscle, date, sets_json, duration, calories
-- FROM workout_logs
-- WHERE user_id = $1 AND date >= CURRENT_DATE - 7
-- ORDER BY date DESC, logged_at DESC;

-- Monthly food summary:
-- SELECT meal_type,
--        SUM(calories) AS total_cal,
--        SUM(protein_g) AS total_protein,
--        SUM(carbs_g) AS total_carbs,
--        SUM(fat_g) AS total_fat
-- FROM food_logs
-- WHERE user_id = $1
--   AND log_date >= DATE_TRUNC('month', CURRENT_DATE)
-- GROUP BY meal_type;

-- Unacknowledged critical alerts:
-- SELECT u.name, u.email, ha.alert_type, ha.severity, ha.message, ha.created_at
-- FROM health_alerts ha
-- JOIN users u ON u.id = ha.user_id
-- WHERE ha.acknowledged = FALSE AND ha.severity = 'critical'
-- ORDER BY ha.created_at DESC;
