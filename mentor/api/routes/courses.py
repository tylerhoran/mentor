"""Course management routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentFaculty, CurrentUser, DbSession
from mentor.models import Concept, Course, CourseEnrollment, Misconception
from mentor.schemas.course import (
    ConceptCreate,
    ConceptResponse,
    ConceptUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    MisconceptionCreate,
    MisconceptionResponse,
)

router = APIRouter(prefix="/courses", tags=["courses"])


# Course CRUD
@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> Course:
    """Create a new course."""
    course = Course(
        name=course_data.name,
        description=course_data.description,
        created_by=current_user.id,
        institution_id=course_data.institution_id or current_user.institution_id,
        pedagogy_config=course_data.pedagogy_config.model_dump()
        if course_data.pedagogy_config
        else {},
        base_model=course_data.base_model,
        temperature=course_data.temperature,
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> list[Course]:
    """List courses accessible to the current user."""
    query = select(Course)

    if current_user.is_faculty:
        # Faculty see courses they created
        query = query.where(Course.created_by == current_user.id)
    elif current_user.is_student:
        # Students see courses they're enrolled in
        query = query.join(CourseEnrollment).where(CourseEnrollment.student_id == current_user.id)
    elif (current_user.is_admin or current_user.is_researcher) and current_user.institution_id:
        # Admin/researchers see all courses in their institution
        query = query.where(Course.institution_id == current_user.institution_id)

    if not include_archived:
        query = query.where(Course.status != "archived")

    result = await db.execute(query.order_by(Course.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> Course:
    """Get a specific course."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check access
    if current_user.is_student:
        enrollment = await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.student_id == current_user.id,
            )
        )
        if not enrollment.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not enrolled in this course")
    elif current_user.is_faculty and course.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return course


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> Course:
    """Update a course."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = course_data.model_dump(exclude_unset=True)
    if "pedagogy_config" in update_data and update_data["pedagogy_config"]:
        update_data["pedagogy_config"] = update_data["pedagogy_config"].model_dump()

    for field, value in update_data.items():
        setattr(course, field, value)

    await db.flush()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> None:
    """Delete a course."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(course)


# Concept CRUD
@router.post(
    "/{course_id}/concepts",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_concept(
    course_id: str,
    concept_data: ConceptCreate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> Concept:
    """Create a concept in a course."""
    # Verify course access
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    concept = Concept(
        course_id=course_id,
        name=concept_data.name,
        description=concept_data.description,
        prerequisites=concept_data.prerequisites,
        estimated_time_minutes=concept_data.estimated_time_minutes,
        difficulty_level=concept_data.difficulty_level,
        learning_objectives=[obj.model_dump() for obj in concept_data.learning_objectives],
        sequence_order=concept_data.sequence_order,
    )
    db.add(concept)
    await db.flush()
    await db.refresh(concept)
    return concept


@router.get("/{course_id}/concepts", response_model=list[ConceptResponse])
async def list_concepts(
    course_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Concept]:
    """List concepts in a course."""
    # Verify course access
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(
        select(Concept)
        .where(Concept.course_id == course_id)
        .order_by(Concept.sequence_order, Concept.created_at)
    )
    return list(result.scalars().all())


@router.get("/{course_id}/concepts/{concept_id}", response_model=ConceptResponse)
async def get_concept(
    course_id: str,
    concept_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> Concept:
    """Get a specific concept."""
    result = await db.execute(
        select(Concept).where(Concept.id == concept_id, Concept.course_id == course_id)
    )
    concept = result.scalar_one_or_none()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    return concept


@router.patch("/{course_id}/concepts/{concept_id}", response_model=ConceptResponse)
async def update_concept(
    course_id: str,
    concept_id: str,
    concept_data: ConceptUpdate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> Concept:
    """Update a concept."""
    result = await db.execute(
        select(Concept)
        .where(Concept.id == concept_id, Concept.course_id == course_id)
        .options(selectinload(Concept.course))
    )
    concept = result.scalar_one_or_none()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    if concept.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = concept_data.model_dump(exclude_unset=True)
    if "learning_objectives" in update_data and update_data["learning_objectives"]:
        update_data["learning_objectives"] = [
            obj.model_dump() for obj in update_data["learning_objectives"]
        ]

    for field, value in update_data.items():
        setattr(concept, field, value)

    await db.flush()
    await db.refresh(concept)
    return concept


@router.delete(
    "/{course_id}/concepts/{concept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_concept(
    course_id: str,
    concept_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> None:
    """Delete a concept."""
    result = await db.execute(
        select(Concept)
        .where(Concept.id == concept_id, Concept.course_id == course_id)
        .options(selectinload(Concept.course))
    )
    concept = result.scalar_one_or_none()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    if concept.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(concept)


# Misconception CRUD
@router.post(
    "/{course_id}/concepts/{concept_id}/misconceptions",
    response_model=MisconceptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_misconception(
    course_id: str,
    concept_id: str,
    misconception_data: MisconceptionCreate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> Misconception:
    """Create a misconception for a concept."""
    result = await db.execute(
        select(Concept)
        .where(Concept.id == concept_id, Concept.course_id == course_id)
        .options(selectinload(Concept.course))
    )
    concept = result.scalar_one_or_none()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    if concept.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    misconception = Misconception(
        concept_id=concept_id,
        **misconception_data.model_dump(),
    )
    db.add(misconception)
    await db.flush()
    await db.refresh(misconception)
    return misconception


@router.get(
    "/{course_id}/concepts/{concept_id}/misconceptions",
    response_model=list[MisconceptionResponse],
)
async def list_misconceptions(
    course_id: str,
    concept_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Misconception]:
    """List misconceptions for a concept."""
    result = await db.execute(
        select(Misconception)
        .join(Concept)
        .where(Concept.id == concept_id, Concept.course_id == course_id)
    )
    return list(result.scalars().all())
