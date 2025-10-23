import enum

class RoleType(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"

class GradeLevel(str, enum.Enum):
    VORSCHULE = "vorschule"
    KLASSE_1 = "klasse_1"
    KLASSE_2 = "klasse_2"
    KLASSE_3 = "klasse_3"
    KLASSE_4 = "klasse_4"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"