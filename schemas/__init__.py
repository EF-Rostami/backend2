# ============================================================
# schemas/__init__.py
# ============================================================
from schemas.user import UserCreate, UserResponse, UserInfoResponse
from schemas.auth import Token, UserLogin, RefreshTokenRequest, SessionInfo
from schemas.student import StudentCreate, StudentResponse, ParentResponse
from schemas.teacher import TeacherCreate, TeacherResponse
from schemas.academic import (
    ClassCreate, ClassResponse,
    CourseCreate, CourseResponse,
    ExamCreate, ExamResponse,
    GradeCreate, GradeResponse, GradeWithDetailsResponse
)
from schemas.attendance import AttendanceCreate, AttendanceResponse
from schemas.fees import FeeRecordCreate, FeeRecordResponse
from schemas.registration import RegistrationRequestCreate, RegistrationRequestResponse
from schemas.admission import (
    AdmissionLetterCreate, AdmissionLetterResponse,
    BulkAdmissionLetterCreate, BulkAdmissionLetterResponse,
    AdmissionVerifyRequest, AdmissionVerifyResponse,
    AdmissionRegisterRequest, AdmissionRegisterResponse,
    AdmissionStatusResponse, StudentAdmissionResponse,
    AdmissionApprovalRequest, AdmissionApprovalResponse,
    AdmissionRejectionRequest, AdmissionRejectionResponse
)
from schemas.absence_excuse import( 
    AbsenceExcuseCreate, AbsenceExcuseDetailResponse,
    AbsenceExcuseResponse, AbsenceExcuseUpdate
)
from schemas.appointment import (
    AppointmentCreate,AppointmentStatus,
    MeetingSummaryCreate, TeacherAvailabilityCreate
)

from schemas.event import(
    EventCreate, EventUpdate,
    EventCancel, EventResponse, EventDetailResponse,
    RSVPCreate, RSVPUpdate, RSVPResponse, AttachmentResponse
)


__all__ = [
    # User
    "UserCreate", "UserResponse", "UserInfoResponse",
    # Auth
    "Token", "UserLogin", "RefreshTokenRequest", "SessionInfo",
    # Student
    "StudentCreate", "StudentResponse", "ParentResponse",
    # Teacher
    "TeacherCreate", "TeacherResponse",
    # Academic
    "ClassCreate", "ClassResponse",
    "CourseCreate", "CourseResponse",
    "ExamCreate", "ExamResponse",
    "GradeCreate", "GradeResponse", "GradeWithDetailsResponse",
    # Attendance
    "AttendanceCreate", "AttendanceResponse",
    # Fees
    "FeeRecordCreate", "FeeRecordResponse",
    # Registration
    "RegistrationRequestCreate", "RegistrationRequestResponse",
    # Admission
    "AdmissionLetterCreate", "AdmissionLetterResponse",
    "BulkAdmissionLetterCreate", "BulkAdmissionLetterResponse",
    "AdmissionVerifyRequest", "AdmissionVerifyResponse",
    "AdmissionRegisterRequest", "AdmissionRegisterResponse",
    "AdmissionStatusResponse", "StudentAdmissionResponse",
    "AdmissionApprovalRequest", "AdmissionApprovalResponse",
    "AdmissionRejectionRequest", "AdmissionRejectionResponse",
    #absence_excuse
    "AbsenceExcuseCreate", "AbsenceExcuseDetailResponse",
    "AbsenceExcuseResponse", "AbsenceExcuseUpdate",
    #appointment
    "AppointmentCreate", "AppointmentStatus",
    "MeetingSummaryCreate", "TeacherAvailabilityCreate"
    #event
    "EventCreate", "EventUpdate",
    "EventCancel", "EventResponse", "EventDetailResponse",
    "RSVPCreate", "RSVPUpdate", "RSVPResponse", "AttachmentResponse"

]

