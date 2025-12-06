"""Analytics routes for faculty dashboards."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentFaculty, DbSession
from mentor.models import Concept, Course, CourseEnrollment, Interaction, StudentState
from mentor.schemas.analytics import (
    ClassOverview,
    ConceptStruggle,
    EngagementStats,
    MasteryDistribution,
    ProgressTimeline,
    StudentProgressResponse,
    StudentSummary,
    TimeSeriesDataPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/course/{course_id}/overview", response_model=ClassOverview)
async def get_class_overview(
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> ClassOverview:
    """Get class-wide analytics overview."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get all student states
    result = await db.execute(select(StudentState).where(StudentState.course_id == course_id))
    states = list(result.scalars().all())

    # Get concepts
    result = await db.execute(select(Concept).where(Concept.course_id == course_id))
    concepts = {c.id: c for c in result.scalars().all()}

    total_students = len(states)
    if total_students == 0:
        # Return empty overview
        return ClassOverview(
            course_id=course_id,
            course_name=course.name,
            total_students=0,
            active_students=0,
            average_mastery=0.0,
            mastery_distribution=[],
            engagement=EngagementStats(
                total_interactions=0,
                total_time_minutes=0.0,
                average_session_length_minutes=0.0,
                session_count=0,
                average_response_time_ms=None,
                last_active=None,
            ),
            struggling_concepts=[],
            students_with_gaming_flags=0,
            completion_rate=0.0,
            generated_at=datetime.now(UTC),
        )

    # Calculate active students (last 7 days)
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    active_students = sum(
        1
        for s in states
        if s.engagement_metrics.get("last_session_at")
        and datetime.fromisoformat(s.engagement_metrics["last_session_at"].replace("Z", "+00:00"))
        > seven_days_ago
    )

    # Calculate average mastery
    all_mastery = []
    for state in states:
        for mastery_data in state.concept_mastery.values():
            all_mastery.append(mastery_data.get("estimate", 0.0))
    average_mastery = sum(all_mastery) / len(all_mastery) if all_mastery else 0.0

    # Build mastery distribution per concept
    mastery_distribution = []
    for concept_id, concept in concepts.items():
        buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
        mastery_values = []

        for state in states:
            if concept_id in state.concept_mastery:
                estimate = state.concept_mastery[concept_id].get("estimate", 0.0)
                mastery_values.append(estimate)
                if estimate < 0.2:
                    buckets["0-20"] += 1
                elif estimate < 0.4:
                    buckets["20-40"] += 1
                elif estimate < 0.6:
                    buckets["40-60"] += 1
                elif estimate < 0.8:
                    buckets["60-80"] += 1
                else:
                    buckets["80-100"] += 1

        mastery_distribution.append(
            MasteryDistribution(
                concept_id=concept_id,
                concept_name=concept.name,
                mastery_buckets=buckets,
                average_mastery=sum(mastery_values) / len(mastery_values)
                if mastery_values
                else 0.0,
                student_count=len(mastery_values),
            )
        )

    # Calculate engagement stats
    total_interactions = sum(s.engagement_metrics.get("total_interactions", 0) for s in states)
    total_time_seconds = sum(s.engagement_metrics.get("total_time_seconds", 0) for s in states)
    total_sessions = sum(s.engagement_metrics.get("session_count", 0) for s in states)
    avg_session_length = (total_time_seconds / total_sessions / 60) if total_sessions > 0 else 0.0

    engagement = EngagementStats(
        total_interactions=total_interactions,
        total_time_minutes=total_time_seconds / 60,
        average_session_length_minutes=avg_session_length,
        session_count=total_sessions,
        average_response_time_ms=None,  # TODO: Calculate from interactions
        last_active=max(
            (
                datetime.fromisoformat(
                    s.engagement_metrics["last_session_at"].replace("Z", "+00:00")
                )
                for s in states
                if s.engagement_metrics.get("last_session_at")
            ),
            default=None,
        ),
    )

    # Find struggling concepts (< 40% average mastery)
    struggling_concepts = []
    for dist in mastery_distribution:
        if dist.average_mastery < 0.4 and dist.student_count > 0:
            struggling_concepts.append(
                ConceptStruggle(
                    concept_id=dist.concept_id,
                    concept_name=dist.concept_name,
                    struggle_rate=(dist.mastery_buckets["0-20"] + dist.mastery_buckets["20-40"])
                    / dist.student_count,
                    common_misconceptions=[],  # TODO: Pull from misconception data
                    average_time_to_mastery_minutes=None,
                )
            )

    # Count students with gaming flags
    students_with_gaming_flags = sum(1 for s in states if s.has_gaming_flags)

    # Calculate completion rate
    students_completed = sum(1 for s in states if len(s.concepts_completed or []) >= len(concepts))
    completion_rate = students_completed / total_students if total_students > 0 else 0.0

    return ClassOverview(
        course_id=course_id,
        course_name=course.name,
        total_students=total_students,
        active_students=active_students,
        average_mastery=average_mastery,
        mastery_distribution=mastery_distribution,
        engagement=engagement,
        struggling_concepts=struggling_concepts,
        students_with_gaming_flags=students_with_gaming_flags,
        completion_rate=completion_rate,
        generated_at=datetime.now(UTC),
    )


@router.get("/course/{course_id}/students", response_model=list[StudentSummary])
async def get_student_summaries(
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
    sort_by: str = "mastery",
    order: str = "desc",
) -> list[StudentSummary]:
    """Get summary of all students in a course."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get all enrollments with student info
    result = await db.execute(
        select(CourseEnrollment)
        .where(CourseEnrollment.course_id == course_id)
        .options(selectinload(CourseEnrollment.student))
    )
    enrollments = list(result.scalars().all())

    # Get student states
    student_ids = [e.student_id for e in enrollments]
    result = await db.execute(
        select(StudentState).where(
            StudentState.course_id == course_id,
            StudentState.student_id.in_(student_ids),
        )
    )
    states = {s.student_id: s for s in result.scalars().all()}

    # Get concept count
    result = await db.execute(
        select(func.count()).select_from(Concept).where(Concept.course_id == course_id)
    )
    total_concepts = result.scalar() or 0

    summaries = []
    for enrollment in enrollments:
        state = states.get(enrollment.student_id)

        if state:
            mastery_values = [m.get("estimate", 0.0) for m in state.concept_mastery.values()]
            overall_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0.0

            engagement = EngagementStats(
                total_interactions=state.engagement_metrics.get("total_interactions", 0),
                total_time_minutes=state.engagement_metrics.get("total_time_seconds", 0) / 60,
                average_session_length_minutes=0.0,  # TODO: Calculate
                session_count=state.engagement_metrics.get("session_count", 0),
                average_response_time_ms=state.engagement_metrics.get("average_response_time_ms"),
                last_active=datetime.fromisoformat(
                    state.engagement_metrics["last_session_at"].replace("Z", "+00:00")
                )
                if state.engagement_metrics.get("last_session_at")
                else None,
            )

            high_severity = len(state.high_severity_flags)
        else:
            overall_mastery = 0.0
            engagement = EngagementStats(
                total_interactions=0,
                total_time_minutes=0.0,
                average_session_length_minutes=0.0,
                session_count=0,
                average_response_time_ms=None,
                last_active=None,
            )
            high_severity = 0

        summaries.append(
            StudentSummary(
                student_id=enrollment.student_id,
                student_name=enrollment.student.full_name,
                overall_mastery=overall_mastery,
                concepts_completed=len(state.concepts_completed or []) if state else 0,
                total_concepts=total_concepts,
                engagement=engagement,
                has_gaming_flags=state.has_gaming_flags if state else False,
                high_severity_flags=high_severity,
                last_interaction=engagement.last_active,
            )
        )

    # Sort results
    reverse = order == "desc"
    if sort_by == "mastery":
        summaries.sort(key=lambda s: s.overall_mastery, reverse=reverse)
    elif sort_by == "interactions":
        summaries.sort(key=lambda s: s.engagement.total_interactions, reverse=reverse)
    elif sort_by == "name":
        summaries.sort(key=lambda s: s.student_name or "", reverse=reverse)

    return summaries


@router.get("/student/{student_id}/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str,
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> StudentProgressResponse:
    """Get detailed progress for a specific student."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get enrollment
    result = await db.execute(
        select(CourseEnrollment)
        .where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == student_id,
        )
        .options(selectinload(CourseEnrollment.student))
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not enrolled")

    # Get student state
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == student_id,
            StudentState.course_id == course_id,
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="Student state not found")

    # Calculate overall mastery
    mastery_values = [m.get("estimate", 0.0) for m in state.concept_mastery.values()]
    overall_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0.0

    engagement = EngagementStats(
        total_interactions=state.engagement_metrics.get("total_interactions", 0),
        total_time_minutes=state.engagement_metrics.get("total_time_seconds", 0) / 60,
        average_session_length_minutes=0.0,
        session_count=state.engagement_metrics.get("session_count", 0),
        average_response_time_ms=state.engagement_metrics.get("average_response_time_ms"),
        last_active=datetime.fromisoformat(
            state.engagement_metrics["last_session_at"].replace("Z", "+00:00")
        )
        if state.engagement_metrics.get("last_session_at")
        else None,
    )

    # Determine trajectory classification
    high_severity = len(state.high_severity_flags)
    if high_severity >= 3:
        trajectory_classification = "suspected_gaming"
    elif high_severity >= 1:
        trajectory_classification = "unclear"
    else:
        trajectory_classification = "genuine"

    # Check for pending verification
    from mentor.models import VerificationReport

    result = await db.execute(
        select(VerificationReport).where(
            VerificationReport.student_id == student_id,
            VerificationReport.course_id == course_id,
            VerificationReport.verification_status == "pending",
        )
    )
    pending_verification = result.scalar_one_or_none() is not None

    # Get last verification
    result = await db.execute(
        select(VerificationReport)
        .where(
            VerificationReport.student_id == student_id,
            VerificationReport.course_id == course_id,
            VerificationReport.verification_status == "completed",
        )
        .order_by(VerificationReport.verified_at.desc())
        .limit(1)
    )
    last_report = result.scalar_one_or_none()

    return StudentProgressResponse(
        student_id=student_id,
        student_name=enrollment.student.full_name,
        course_id=course_id,
        enrolled_at=enrollment.enrolled_at,
        study_condition=enrollment.study_condition,
        overall_mastery=overall_mastery,
        concept_mastery=state.concept_mastery,
        concepts_completed=state.concepts_completed or [],
        current_concept_id=state.current_concept_id,
        engagement=engagement,
        gaming_flags=state.gaming_flags,
        trajectory_classification=trajectory_classification,
        pending_verification=pending_verification,
        last_verification=last_report.verified_at if last_report else None,
    )


@router.get("/student/{student_id}/timeline", response_model=ProgressTimeline)
async def get_student_timeline(
    student_id: str,
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> ProgressTimeline:
    """Get timeline of student progress."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get interactions grouped by day
    result = await db.execute(
        select(Interaction)
        .where(
            Interaction.student_id == student_id,
            Interaction.course_id == course_id,
        )
        .order_by(Interaction.timestamp)
    )
    interactions = list(result.scalars().all())

    # Build interactions per day
    interactions_by_day: dict[str, int] = {}
    for interaction in interactions:
        day = interaction.timestamp.date().isoformat()
        interactions_by_day[day] = interactions_by_day.get(day, 0) + 1

    interactions_per_day = [
        TimeSeriesDataPoint(
            timestamp=datetime.fromisoformat(day),
            value=float(count),
        )
        for day, count in sorted(interactions_by_day.items())
    ]

    # TODO: Build mastery over time from historical data
    # For now, return empty
    mastery_over_time: list[TimeSeriesDataPoint] = []

    # TODO: Track concept completions over time
    concept_completions: list[dict] = []

    return ProgressTimeline(
        student_id=student_id,
        course_id=course_id,
        mastery_over_time=mastery_over_time,
        interactions_per_day=interactions_per_day,
        concept_completions=concept_completions,
    )
