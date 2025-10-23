# ============================================================
# services/__init__.py
# ============================================================
from services.email_service import (
    send_admission_pending_email,
    send_admission_approval_email,
    send_admission_rejection_email
)
from services.admission_service import generate_admission_number

__all__ = [
    "send_admission_pending_email",
    "send_admission_approval_email",
    "send_admission_rejection_email",
    "generate_admission_number"
]