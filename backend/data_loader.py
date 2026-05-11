import os
import sqlite3
import pandas as pd
from config import REFERENCE_DATE

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


def load_all_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # Clear existing rows in reverse dependency order
    for table in ("encounters", "labs", "diagnoses", "patients"):
        cursor.execute(f"DELETE FROM {table}")
    conn.commit()

    # --- patients ---
    patients = pd.read_csv(os.path.join(DATA_DIR, "patients.csv"))
    patients.to_sql("patients", conn, if_exists="append", index=False)
    print(f"patients loaded: {len(patients)}")

    # --- diagnoses ---
    diagnoses = pd.read_csv(os.path.join(DATA_DIR, "diagnoses.csv"))
    diagnoses.to_sql("diagnoses", conn, if_exists="append", index=False)
    print(f"diagnoses loaded: {len(diagnoses)}")

    # --- labs ---
    labs = pd.read_csv(os.path.join(DATA_DIR, "labs.csv"))
    labs.to_sql("labs", conn, if_exists="append", index=False)
    print(f"labs loaded: {len(labs)}")

    # --- encounters ---
    encounters = pd.read_csv(os.path.join(DATA_DIR, "encounters.csv"))
    encounters["encounter_date"] = pd.to_datetime(encounters["encounter_date"]).dt.date
    encounters["is_future"] = encounters["encounter_date"].apply(
        lambda d: 1 if d > REFERENCE_DATE else 0
    )
    encounters["encounter_date"] = encounters["encounter_date"].apply(
        lambda d: d.strftime("%Y-%m-%d")
    )

    encounters.to_sql("encounters", conn, if_exists="append", index=False)

    past = int((encounters["is_future"] == 0).sum())
    future = int((encounters["is_future"] == 1).sum())
    print(f"encounters loaded: {len(encounters)} (past: {past}, future: {future})")
