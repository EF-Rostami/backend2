from sqlalchemy.orm import Session
from models import AdmissionLetter
from utils.enums import GradeLevel

def generate_admission_number(grade_level: GradeLevel, academic_year: str, db: Session) -> str:
    """
    Generate admission number in format: G1-2025-001
    """
    grade_map = {
        GradeLevel.VORSCHULE: "V",
        GradeLevel.KLASSE_1: "G1",
        GradeLevel.KLASSE_2: "G2",
        GradeLevel.KLASSE_3: "G3",
        GradeLevel.KLASSE_4: "G4",
    }
    
    grade_code = grade_map.get(grade_level, "G1")
    year = academic_year.split("-")[0] if "-" in academic_year else academic_year
    
    # Find the last admission number for this grade and year
    last_admission = db.query(AdmissionLetter).filter(
        AdmissionLetter.grade_level == grade_level,
        AdmissionLetter.academic_year == academic_year
    ).order_by(AdmissionLetter.id.desc()).first()
    
    if last_admission:
        last_number = int(last_admission.admission_number.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{grade_code}-{year}-{new_number:03d}"