# Copy your email_service.py content here
# This should be the same as your existing email_service.py file

async def send_admission_pending_email(
    to_email: str,
    parent_name: str,
    child_name: str,
    admission_number: str
):
    """Send email when admission is submitted"""
    # Implement your email sending logic
    pass

async def send_admission_approval_email(
    to_email: str,
    parent_name: str,
    child_name: str,
    admission_number: str,
    parent_username: str,
    parent_password: str,
    student_username: str,
    student_password: str,
    portal_url: str
):
    """Send email when admission is approved"""
    # Implement your email sending logic
    pass

async def send_admission_rejection_email(
    to_email: str,
    parent_name: str,
    child_name: str,
    admission_number: str,
    reason: str
):
    """Send email when admission is rejected"""
    # Implement your email sending logic
    pass




