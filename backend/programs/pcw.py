from typing import List
from rules_engine import ClinicalNeed, ClinicalProgram, PROGRAM_REGISTRY
from config import REFERENCE_DATE

CHRONIC_PREFIXES = [
    "E10", "E11", "I10", "E78", "J45",
    "N18", "I25", "E03", "G47.3", "M81",
]


def _calc_age(date_of_birth_str: str) -> int:
    from datetime import date
    dob = date.fromisoformat(date_of_birth_str)
    age = REFERENCE_DATE.year - dob.year
    if (REFERENCE_DATE.month, REFERENCE_DATE.day) < (dob.month, dob.day):
        age -= 1
    return age


def _has_chronic(icd_codes: list) -> bool:
    for code in icd_codes:
        for prefix in CHRONIC_PREFIXES:
            if code.startswith(prefix):
                return True
    return False


class PrimaryCareWellness(ClinicalProgram):
    program_name = "Primary Care Wellness"

    def check_eligibility(self, patient_id: str, conn) -> bool:
        row = conn.execute(
            "SELECT date_of_birth FROM patients WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
        if row is None:
            return False
        return _calc_age(row["date_of_birth"]) >= 18

    def get_tier(self, patient_id: str, conn) -> str:
        row = conn.execute(
            "SELECT date_of_birth FROM patients WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
        if _calc_age(row["date_of_birth"]) >= 65:
            return "High Priority"

        rows = conn.execute(
            "SELECT icd_code FROM diagnoses WHERE patient_id = ?",
            (patient_id,),
        ).fetchall()
        icd_codes = [r["icd_code"] for r in rows]
        if _has_chronic(icd_codes):
            return "High Priority"

        return "Standard"

    def get_needs(self, tier: str) -> List[ClinicalNeed]:
        if tier == "High Priority":
            return [ClinicalNeed(specialty="PCP", cadence_days=180)]
        return [ClinicalNeed(specialty="PCP", cadence_days=365)]


PROGRAM_REGISTRY.append(PrimaryCareWellness())
