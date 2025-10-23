from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from dependencies import get_current_user, require_roles, get_user_roles
from models import User, Event, EventRSVP, Student, Parent, StudentParent
from schemas.event import (
    EventCreate, EventUpdate, EventCancel, EventResponse, EventDetailResponse,
    RSVPCreate, RSVPUpdate, RSVPResponse
)

router = APIRouter(prefix="/events", tags=["events"])

# ==================== EVENT MANAGEMENT ====================

@router.post("", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Create a new event (admin/teacher only).
    """
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        location=event_data.location,
        target_audience=event_data.target_audience,
        target_grade_levels=event_data.target_grade_levels,
        requires_rsvp=event_data.requires_rsvp,
        max_participants=event_data.max_participants,
        registration_deadline=event_data.registration_deadline,
        created_by=current_user.id,
        organizer_name=event_data.organizer_name or f"{current_user.firstName} {current_user.lastName}",
        organizer_contact=event_data.organizer_contact,
        is_published=event_data.is_published
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return EventResponse(
        id=new_event.id,
        title=new_event.title,
        description=new_event.description,
        event_type=new_event.event_type.value if hasattr(new_event.event_type, 'value') else new_event.event_type,
        start_date=new_event.start_date,
        end_date=new_event.end_date,
        location=new_event.location,
        target_audience=new_event.target_audience.value if hasattr(new_event.target_audience, 'value') else new_event.target_audience,
        target_grade_levels=new_event.target_grade_levels,
        requires_rsvp=new_event.requires_rsvp,
        max_participants=new_event.max_participants,
        registration_deadline=new_event.registration_deadline,
        created_by=new_event.created_by,
        organizer_name=new_event.organizer_name,
        organizer_contact=new_event.organizer_contact,
        is_published=new_event.is_published,
        is_cancelled=new_event.is_cancelled,
        cancellation_reason=new_event.cancellation_reason,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

@router.get("", response_model=List[EventDetailResponse])
async def get_events(
    event_type: Optional[str] = Query(None),
    target_audience: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_cancelled: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all events with optional filters.
    """
    user_roles = get_user_roles(current_user)
    
    # Base query - only published events for non-admin/teacher
    query = db.query(Event)
    
    if "admin" not in user_roles and "teacher" not in user_roles:
        query = query.filter(Event.is_published == True)
    
    # Filter cancelled events
    if not include_cancelled:
        query = query.filter(Event.is_cancelled == False)
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if target_audience:
        query = query.filter(
            or_(
                Event.target_audience == target_audience,
                Event.target_audience == "all"
            )
        )
    
    if start_date:
        query = query.filter(Event.start_date >= start_date)
    
    if end_date:
        query = query.filter(Event.end_date <= end_date)
    
    events = query.order_by(Event.start_date.asc()).offset(skip).limit(limit).all()
    
    result = []
    for event in events:
        # Get creator info
        creator = db.query(User).filter(User.id == event.created_by).first()
        creator_name = f"{creator.firstName} {creator.lastName}" if creator else "Unknown"
        
        # Get RSVP stats
        total_rsvps = db.query(EventRSVP).filter(EventRSVP.event_id == event.id).count()
        attending_count = db.query(EventRSVP).filter(
            EventRSVP.event_id == event.id,
            EventRSVP.status == "attending"
        ).count()
        
        # Calculate available spots
        available_spots = None
        if event.max_participants:
            available_spots = max(0, event.max_participants - attending_count)
        
        # Get user's RSVP status
        user_rsvp = db.query(EventRSVP).filter(
            EventRSVP.event_id == event.id,
            EventRSVP.user_id == current_user.id
        ).first()
        user_rsvp_status = user_rsvp.status.value if user_rsvp and hasattr(user_rsvp.status, 'value') else (user_rsvp.status if user_rsvp else None)
        
        result.append(EventDetailResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            event_type=event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
            start_date=event.start_date,
            end_date=event.end_date,
            location=event.location,
            target_audience=event.target_audience.value if hasattr(event.target_audience, 'value') else event.target_audience,
            target_grade_levels=event.target_grade_levels,
            requires_rsvp=event.requires_rsvp,
            max_participants=event.max_participants,
            registration_deadline=event.registration_deadline,
            created_by=event.created_by,
            creator_name=creator_name,
            organizer_name=event.organizer_name,
            organizer_contact=event.organizer_contact,
            is_published=event.is_published,
            is_cancelled=event.is_cancelled,
            cancellation_reason=event.cancellation_reason,
            created_at=event.created_at,
            updated_at=event.updated_at,
            total_rsvps=total_rsvps,
            attending_count=attending_count,
            available_spots=available_spots,
            user_rsvp_status=user_rsvp_status
        ))
    
    return result

@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific event.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    user_roles = get_user_roles(current_user)
    
    # Check if user can access unpublished events
    if not event.is_published and "admin" not in user_roles and "teacher" not in user_roles:
        raise HTTPException(status_code=403, detail="Event not published")
    
    # Get creator info
    creator = db.query(User).filter(User.id == event.created_by).first()
    creator_name = f"{creator.firstName} {creator.lastName}" if creator else "Unknown"
    
    # Get RSVP stats
    total_rsvps = db.query(EventRSVP).filter(EventRSVP.event_id == event.id).count()
    attending_count = db.query(EventRSVP).filter(
        EventRSVP.event_id == event.id,
        EventRSVP.status == "attending"
    ).count()
    
    # Calculate available spots
    available_spots = None
    if event.max_participants:
        available_spots = max(0, event.max_participants - attending_count)
    
    # Get user's RSVP status
    user_rsvp = db.query(EventRSVP).filter(
        EventRSVP.event_id == event.id,
        EventRSVP.user_id == current_user.id
    ).first()
    user_rsvp_status = user_rsvp.status.value if user_rsvp and hasattr(user_rsvp.status, 'value') else (user_rsvp.status if user_rsvp else None)
    
    return EventDetailResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        target_audience=event.target_audience.value if hasattr(event.target_audience, 'value') else event.target_audience,
        target_grade_levels=event.target_grade_levels,
        requires_rsvp=event.requires_rsvp,
        max_participants=event.max_participants,
        registration_deadline=event.registration_deadline,
        created_by=event.created_by,
        creator_name=creator_name,
        organizer_name=event.organizer_name,
        organizer_contact=event.organizer_contact,
        is_published=event.is_published,
        is_cancelled=event.is_cancelled,
        cancellation_reason=event.cancellation_reason,
        created_at=event.created_at,
        updated_at=event.updated_at,
        total_rsvps=total_rsvps,
        attending_count=attending_count,
        available_spots=available_spots,
        user_rsvp_status=user_rsvp_status
    )

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Update an event (admin/teacher only).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields if provided
    if event_data.title is not None:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.event_type is not None:
        event.event_type = event_data.event_type
    if event_data.start_date is not None:
        event.start_date = event_data.start_date
    if event_data.end_date is not None:
        event.end_date = event_data.end_date
    if event_data.location is not None:
        event.location = event_data.location
    if event_data.target_audience is not None:
        event.target_audience = event_data.target_audience
    if event_data.target_grade_levels is not None:
        event.target_grade_levels = event_data.target_grade_levels
    if event_data.requires_rsvp is not None:
        event.requires_rsvp = event_data.requires_rsvp
    if event_data.max_participants is not None:
        event.max_participants = event_data.max_participants
    if event_data.registration_deadline is not None:
        event.registration_deadline = event_data.registration_deadline
    if event_data.organizer_name is not None:
        event.organizer_name = event_data.organizer_name
    if event_data.organizer_contact is not None:
        event.organizer_contact = event_data.organizer_contact
    if event_data.is_published is not None:
        event.is_published = event_data.is_published
    
    event.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        target_audience=event.target_audience.value if hasattr(event.target_audience, 'value') else event.target_audience,
        target_grade_levels=event.target_grade_levels,
        requires_rsvp=event.requires_rsvp,
        max_participants=event.max_participants,
        registration_deadline=event.registration_deadline,
        created_by=event.created_by,
        organizer_name=event.organizer_name,
        organizer_contact=event.organizer_contact,
        is_published=event.is_published,
        is_cancelled=event.is_cancelled,
        cancellation_reason=event.cancellation_reason,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@router.post("/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: int,
    cancel_data: EventCancel,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Cancel an event (admin/teacher only).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.is_cancelled = True
    event.cancellation_reason = cancel_data.cancellation_reason
    event.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        target_audience=event.target_audience.value if hasattr(event.target_audience, 'value') else event.target_audience,
        target_grade_levels=event.target_grade_levels,
        requires_rsvp=event.requires_rsvp,
        max_participants=event.max_participants,
        registration_deadline=event.registration_deadline,
        created_by=event.created_by,
        organizer_name=event.organizer_name,
        organizer_contact=event.organizer_contact,
        is_published=event.is_published,
        is_cancelled=event.is_cancelled,
        cancellation_reason=event.cancellation_reason,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Delete an event (admin only).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}

# ==================== RSVP MANAGEMENT ====================

@router.post("/{event_id}/rsvp", response_model=RSVPResponse)
async def create_rsvp(
    event_id: int,
    rsvp_data: RSVPCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RSVP to an event.
    """
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if event is published and not cancelled
    if not event.is_published:
        raise HTTPException(status_code=403, detail="Event not published")
    
    if event.is_cancelled:
        raise HTTPException(status_code=403, detail="Event is cancelled")
    
    # Check if RSVP is required
    if not event.requires_rsvp:
        raise HTTPException(status_code=400, detail="This event does not require RSVP")
    
    # Check registration deadline
    if event.registration_deadline and datetime.now(timezone.utc) > event.registration_deadline:
        raise HTTPException(status_code=403, detail="Registration deadline has passed")
    
    # Check if event is full
    if event.max_participants:
        attending_count = db.query(EventRSVP).filter(
            EventRSVP.event_id == event_id,
            EventRSVP.status == "attending"
        ).count()
        if attending_count >= event.max_participants and rsvp_data.status == "attending":
            raise HTTPException(status_code=403, detail="Event is full")
    
    # Check if student_id provided for parent
    user_roles = get_user_roles(current_user)
    if rsvp_data.student_id:
        if "parent" not in user_roles:
            raise HTTPException(status_code=403, detail="Only parents can RSVP for students")
        
        # Verify parent-student relationship
        parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
        if not parent:
            raise HTTPException(status_code=403, detail="Parent profile not found")
        
        relationship = db.query(StudentParent).filter(
            StudentParent.student_id == rsvp_data.student_id,
            StudentParent.parent_id == parent.id
        ).first()
        
        if not relationship:
            raise HTTPException(status_code=403, detail="You are not authorized to RSVP for this student")
    
    # Check for existing RSVP
    existing_rsvp = db.query(EventRSVP).filter(
        EventRSVP.event_id == event_id,
        EventRSVP.user_id == current_user.id,
        EventRSVP.student_id == rsvp_data.student_id
    ).first()
    
    if existing_rsvp:
        raise HTTPException(status_code=400, detail="You have already RSVPed to this event")
    
    # Create RSVP
    new_rsvp = EventRSVP(
        event_id=event_id,
        user_id=current_user.id,
        student_id=rsvp_data.student_id,
        status=rsvp_data.status,
        notes=rsvp_data.notes
    )
    
    db.add(new_rsvp)
    db.commit()
    db.refresh(new_rsvp)
    
    # Get user and student names
    user_name = f"{current_user.firstName} {current_user.lastName}"
    student_name = None
    if rsvp_data.student_id:
        student = db.query(Student).filter(Student.id == rsvp_data.student_id).first()
        if student:
            student_user = db.query(User).filter(User.id == student.user_id).first()
            if student_user:
                student_name = f"{student_user.firstName} {student_user.lastName}"
    
    return RSVPResponse(
        id=new_rsvp.id,
        event_id=new_rsvp.event_id,
        user_id=new_rsvp.user_id,
        student_id=new_rsvp.student_id,
        status=new_rsvp.status.value if hasattr(new_rsvp.status, 'value') else new_rsvp.status,
        response_date=new_rsvp.response_date,
        notes=new_rsvp.notes,
        user_name=user_name,
        student_name=student_name
    )

@router.patch("/{event_id}/rsvp", response_model=RSVPResponse)
async def update_rsvp(
    event_id: int,
    rsvp_data: RSVPUpdate,
    student_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing RSVP.
    """
    # Find existing RSVP
    rsvp = db.query(EventRSVP).filter(
        EventRSVP.event_id == event_id,
        EventRSVP.user_id == current_user.id,
        EventRSVP.student_id == student_id
    ).first()
    
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    
    # Update RSVP
    rsvp.status = rsvp_data.status
    rsvp.notes = rsvp_data.notes
    rsvp.response_date = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(rsvp)
    
    # Get user and student names
    user_name = f"{current_user.firstName} {current_user.lastName}"
    student_name = None
    if rsvp.student_id:
        student = db.query(Student).filter(Student.id == rsvp.student_id).first()
        if student:
            student_user = db.query(User).filter(User.id == student.user_id).first()
            if student_user:
                student_name = f"{student_user.firstName} {student_user.lastName}"
    
    return RSVPResponse(
        id=rsvp.id,
        event_id=rsvp.event_id,
        user_id=rsvp.user_id,
        student_id=rsvp.student_id,
        status=rsvp.status.value if hasattr(rsvp.status, 'value') else rsvp.status,
        response_date=rsvp.response_date,
        notes=rsvp.notes,
        user_name=user_name,
        student_name=student_name
    )

@router.get("/{event_id}/rsvps", response_model=List[RSVPResponse])
async def get_event_rsvps(
    event_id: int,
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Get all RSVPs for an event (admin/teacher only).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    query = db.query(EventRSVP).filter(EventRSVP.event_id == event_id)
    
    if status:
        query = query.filter(EventRSVP.status == status)
    
    rsvps = query.order_by(EventRSVP.response_date.desc()).all()
    
    result = []
    for rsvp in rsvps:
        # Get user name
        user = db.query(User).filter(User.id == rsvp.user_id).first()
        user_name = f"{user.firstName} {user.lastName}" if user else "Unknown"
        
        # Get student name if applicable
        student_name = None
        if rsvp.student_id:
            student = db.query(Student).filter(Student.id == rsvp.student_id).first()
            if student:
                student_user = db.query(User).filter(User.id == student.user_id).first()
                if student_user:
                    student_name = f"{student_user.firstName} {student_user.lastName}"
        
        result.append(RSVPResponse(
            id=rsvp.id,
            event_id=rsvp.event_id,
            user_id=rsvp.user_id,
            student_id=rsvp.student_id,
            status=rsvp.status.value if hasattr(rsvp.status, 'value') else rsvp.status,
            response_date=rsvp.response_date,
            notes=rsvp.notes,
            user_name=user_name,
            student_name=student_name
        ))
    
    return result

@router.delete("/{event_id}/rsvp")
async def delete_rsvp(
    event_id: int,
    student_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an RSVP.
    """
    rsvp = db.query(EventRSVP).filter(
        EventRSVP.event_id == event_id,
        EventRSVP.user_id == current_user.id,
        EventRSVP.student_id == student_id
    ).first()
    
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    
    db.delete(rsvp)
    db.commit()
    
    return {"message": "RSVP deleted successfully"}