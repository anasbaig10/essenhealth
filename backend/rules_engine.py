from dataclasses import dataclass, field
from typing import List


@dataclass
class ClinicalNeed:
    specialty: str
    cadence_days: int
    need_type: str = "specialist_visit"


class ClinicalProgram:
    program_name: str = ""

    def check_eligibility(self, patient_id: str, conn) -> bool:
        raise NotImplementedError

    def get_tier(self, patient_id: str, conn) -> str:
        raise NotImplementedError

    def get_needs(self, tier: str) -> List[ClinicalNeed]:
        raise NotImplementedError


PROGRAM_REGISTRY = []
