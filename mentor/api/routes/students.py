"""Student management routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentFaculty, CurrentStudent, DbSession
from mentor.models import Course, CourseEnrollment, StudentState, User

router = APIRouter(prefix="/students", tags=["students"])


class EnrollmentRequest(BaseModel):
    """Request to enroll in a course."""

    course_id: str
    enrollment_code: str | None = None


class EnrollmentResponse(BaseModel):
    """Response for enrollment."""

    id: str
    course_id: str
    student_id: str
    enrolled_at: datetime
    study_condition: str | None

    model_config = {"from_attributes": True}


class StudentProgressResponse(BaseModel):
    """Student progress in a course."""

    student_id: str
    course_id: str
    overall_mastery: float
    concepts_completed: list[str]
    current_concept_id: str | None
    total_interactions: int
    total_time_minutes: float
    has_gaming_flags: bool


class BulkEnrollRequest(BaseModel):
    """Request to bulk enroll students."""

    student_emails: list[str]
    study_condition: str | None = None


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_in_course(
    enrollment: EnrollmentRequest,
    db: DbSession,
    current_user: CurrentStudent,
) -> CourseEnrollment:
    """Enroll current student in a course."""
    # Verify course exists and is active
    result = await db.execute(
        select(Course).where(
            Course.id == enrollment.course_id,
            Course.status == "active",
        )
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not active")

    # Check if already enrolled
    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.course_id == enrollment.course_id,
            CourseEnrollment.student_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    # Create enrollment
    course_enrollment = CourseEnrollment(
        course_id=enrollment.course_id,
        student_id=current_user.id,
    )
    db.add(course_enrollment)

    # Create initial student state
    student_state = StudentState(
        student_id=current_user.id,
        course_id=enrollment.course_id,
    )
    db.add(student_state)

    await db.flush()
    await db.refresh(course_enrollment)

    return course_enrollment


@router.get("/my-courses", response_model=list[EnrollmentResponse])
async def get_my_enrollments(
    db: DbSession,
    current_user: CurrentStudent,
) -> list[CourseEnrollment]:
    """Get current student's course enrollments."""
    result = await db.execute(
        select(CourseEnrollment)
        .where(CourseEnrollment.student_id == current_user.id)
        .options(selectinload(CourseEnrollment.course))
    )
    return list(result.scalars().all())


@router.get("/my-progress/{course_id}", response_model=StudentProgressResponse)
async def get_my_progress(
    course_id: str,
    db: DbSession,
    current_user: CurrentStudent,
) -> StudentProgressResponse:
    """Get current student's progress in a course."""
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == current_user.id,
            StudentState.course_id == course_id,
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    # Calculate overall mastery
    mastery_values = [m.get("estimate", 0.0) for m in state.concept_mastery.values()]
    overall_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0.0

    return StudentProgressResponse(
        student_id=current_user.id,
        course_id=course_id,
        overall_mastery=overall_mastery,
        concepts_completed=state.concepts_completed or [],
        current_concept_id=state.current_concept_id,
        total_interactions=state.engagement_metrics.get("total_interactions", 0),
        total_time_minutes=state.engagement_metrics.get("total_time_seconds", 0) / 60,
        has_gaming_flags=state.has_gaming_flags,
    )


# Faculty routes for managing students
@router.get("/courses/{course_id}/students", response_model=list[dict])
async def list_course_students(
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> list[dict]:
    """List all students enrolled in a course."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get enrollments with student info
    result = await db.execute(
        select(CourseEnrollment)
        .where(CourseEnrollment.course_id == course_id)
        .options(selectinload(CourseEnrollment.student))
    )
    enrollments = result.scalars().all()

    # Get student states
    student_ids = [e.student_id for e in enrollments]
    result = await db.execute(
        select(StudentState).where(
            StudentState.course_id == course_id,
            StudentState.student_id.in_(student_ids),
        )
    )
    states = {s.student_id: s for s in result.scalars().all()}

    students = []
    for enrollment in enrollments:
        state = states.get(enrollment.student_id)
        mastery_values = (
            [m.get("estimate", 0.0) for m in (state.concept_mastery or {}).values()]
            if state
            else []
        )
        overall_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0.0

        students.append(
            {
                "student_id": enrollment.student_id,
                "email": enrollment.student.email,
                "full_name": enrollment.student.full_name,
                "enrolled_at": enrollment.enrolled_at,
                "study_condition": enrollment.study_condition,
                "overall_mastery": overall_mastery,
                "concepts_completed": len(state.concepts_completed or []) if state else 0,
                "total_interactions": state.engagement_metrics.get("total_interactions", 0)
                if state
                else 0,
                "has_gaming_flags": state.has_gaming_flags if state else False,
            }
        )

    return students


@router.post("/courses/{course_id}/students/bulk-enroll")
async def bulk_enroll_students(
    course_id: str,
    request: BulkEnrollRequest,
    db: DbSession,
    current_user: CurrentFaculty,
) -> dict:
    """Bulk enroll students in a course by email."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    enrolled = []
    not_found = []
    already_enrolled = []

    for email in request.student_emails:
        # Find user
        result = await db.execute(select(User).where(User.email == email, User.role == "student"))
        student = result.scalar_one_or_none()

        if not student:
            not_found.append(email)
            continue

        # Check existing enrollment
        result = await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.student_id == student.id,
            )
        )
        if result.scalar_one_or_none():
            already_enrolled.append(email)
            continue

        # Create enrollment
        enrollment = CourseEnrollment(
            course_id=course_id,
            student_id=student.id,
            study_condition=request.study_condition,
        )
        db.add(enrollment)

        # Create student state
        state = StudentState(
            student_id=student.id,
            course_id=course_id,
        )
        db.add(state)

        enrolled.append(email)

    await db.flush()

    return {
        "enrolled": enrolled,
        "not_found": not_found,
        "already_enrolled": already_enrolled,
    }


@router.delete("/courses/{course_id}/students/{student_id}")
async def remove_student(
    course_id: str,
    student_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> dict:
    """Remove a student from a course."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Find enrollment
    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == student_id,
        )
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    await db.delete(enrollment)

    return {"message": "Student removed from course"}
