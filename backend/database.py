import sqlite3

DB_PATH = "./clinical_engine.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id        TEXT PRIMARY KEY,
            first_name        TEXT,
            last_name         TEXT,
            date_of_birth     DATE,
            gender            TEXT,
            phone             TEXT,
            language          TEXT,
            pcp_provider_name TEXT
        );

        CREATE TABLE IF NOT EXISTS diagnoses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT REFERENCES patients(patient_id),
            icd_code        TEXT,
            description     TEXT,
            diagnosed_date  DATE
        );

        CREATE TABLE IF NOT EXISTS labs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id    TEXT REFERENCES patients(patient_id),
            test_name     TEXT,
            result_value  REAL,
            result_date   DATE
        );

        CREATE TABLE IF NOT EXISTS encounters (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT REFERENCES patients(patient_id),
            specialty       TEXT,
            encounter_date  DATE,
            provider_name   TEXT,
            is_future       BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   TEXT REFERENCES patients(patient_id),
            program      TEXT,
            tier         TEXT,
            evaluated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   TEXT REFERENCES patients(patient_id),
            program      TEXT,
            specialty    TEXT,
            task_type    TEXT,
            need_type    TEXT,
            cadence_days INTEGER,
            last_visit   DATE,
            days_overdue INTEGER,
            evaluated_at TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
