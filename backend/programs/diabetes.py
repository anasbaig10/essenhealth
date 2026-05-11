from typing import List
from rules_engine import ClinicalNeed, ClinicalProgram, PROGRAM_REGISTRY
from config import HBAIC_CUTOFF


class DiabetesManagement(ClinicalProgram):
    program_name = "Diabetes Management"

    def check_eligibility(self, patient_id: str, conn) -> bool:
        rows = conn.execute(
            "SELECT icd_code FROM diagnoses WHERE patient_id = ?",
            (patient_id,),
        ).fetchall()
        return any(
            r["icd_code"].startswith("E10") or r["icd_code"].startswith("E11")
            for r in rows
        )

    def get_tier(self, patient_id: str, conn) -> str:
        cutoff_str = HBAIC_CUTOFF.strftime("%Y-%m-%d")
        row = conn.execute(
            """
            SELECT result_value FROM labs
            WHERE patient_id = ?
              AND test_name = 'HbA1c'
              AND result_date >= ?
            ORDER BY result_date DESC
            LIMIT 1
            """,
            (patient_id, cutoff_str),
        ).fetchone()

        if row is None:
            return "Unmonitored"
        value = row["result_value"]
        if value >= 9.0:
            return "High Risk"
        if value >= 7.0:
            return "Moderate Risk"
        return "Low Risk"

    def get_needs(self, tier: str) -> List[ClinicalNeed]:
        if tier == "High Risk":
            return [
                ClinicalNeed("Endocrinology", 90),
                ClinicalNeed("Cardiology", 90),
                ClinicalNeed("Podiatry", 180),
                ClinicalNeed("Ophthalmology", 365),
                ClinicalNeed("Nephrology", 180),
            ]
        if tier == "Moderate Risk":
            return [
                ClinicalNeed("Endocrinology", 180),
                ClinicalNeed("Ophthalmology", 365),
                ClinicalNeed("Podiatry", 365),
            ]
        if tier == "Low Risk":
            return [
                ClinicalNeed("Endocrinology", 365),
                ClinicalNeed("Ophthalmology", 365),
            ]
        # Unmonitored
        return [ClinicalNeed("Endocrinology", 90)]


PROGRAM_REGISTRY.append(DiabetesManagement())
