"""Assessment and verification routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentFaculty, DbSession
from mentor.models import (
    Concept,
    Course,
    Interaction,
    StudentState,
    VerificationReport,
)
from mentor.schemas.assessment import (
    GamingFlag,
    InteractionExcerpt,
    MasteryEstimate,
    MasteryReport,
    TrajectoryAnalysis,
    VerificationQuestion,
    VerificationReportCreate,
    VerificationReportResponse,
    VerificationResults,
)

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/student/{student_id}/mastery", response_model=MasteryReport)
async def get_mastery_report(
    student_id: str,
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> MasteryReport:
    """Get mastery report for a student."""
    # Verify course ownership
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get student state
    state_result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == student_id,
            StudentState.course_id == course_id,
        )
    )
    state = state_result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="Student not enrolled in this course")

    # Get concepts for names
    concepts_result = await db.execute(select(Concept).where(Concept.course_id == course_id))
    concepts: dict[str, Concept] = {c.id: c for c in concepts_result.scalars().all()}

    # Build mastery estimates
    mastery_estimates = []
    for concept_id, mastery_data in state.concept_mastery.items():
        concept = concepts.get(concept_id)
        mastery_estimates.append(
            MasteryEstimate(
                concept_id=concept_id,
                concept_name=concept.name if concept else "Unknown",
                estimate=mastery_data.get("estimate", 0.0),
                confidence=mastery_data.get("confidence", 0.0),
                interaction_count=mastery_data.get("interactions", 0),
                last_updated=mastery_data.get("last_updated"),
            )
        )

    # Calculate overall mastery
    estimates = [m.estimate for m in mastery_estimates]
    overall_mastery = sum(estimates) / len(estimates) if estimates else 0.0
    confidences = [m.confidence for m in mastery_estimates]
    overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return MasteryReport(
        student_id=student_id,
        course_id=course_id,
        overall_mastery=overall_mastery,
        overall_confidence=overall_confidence,
        concepts=mastery_estimates,
        concepts_completed=state.concepts_completed or [],
        current_concept_id=state.current_concept_id,
        generated_at=datetime.now(UTC),
    )


@router.get("/student/{student_id}/trajectory", response_model=TrajectoryAnalysis)
async def get_trajectory_analysis(
    student_id: str,
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> TrajectoryAnalysis:
    """Analyze student's learning trajectory for gaming detection."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get student state
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == student_id,
            StudentState.course_id == course_id,
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="Student not enrolled")

    # Convert gaming flags
    gaming_flags = [
        GamingFlag(
            type=flag.get("type", "unknown"),
            severity=flag.get("severity", "low"),
            timestamp=flag.get("timestamp", datetime.now(UTC)),
            evidence=flag.get("evidence", ""),
            interaction_id=flag.get("interaction_id"),
            resolved=flag.get("resolved", False),
        )
        for flag in state.gaming_flags
    ]

    # Determine classification based on flags
    high_severity_count = sum(1 for f in gaming_flags if f.severity == "high" and not f.resolved)
    if high_severity_count >= 3:
        classification = "suspected_gaming"
        confidence = 0.8
    elif high_severity_count >= 1 or len(gaming_flags) >= 5:
        classification = "unclear"
        confidence = 0.5
    else:
        classification = "genuine"
        confidence = 0.7

    # TODO: Use GamingDetector for actual analysis
    analysis_summary = (
        f"Found {len(gaming_flags)} gaming signals, {high_severity_count} high severity."
    )

    return TrajectoryAnalysis(
        student_id=student_id,
        course_id=course_id,
        classification=classification,
        confidence=confidence,
        gaming_flags=gaming_flags,
        analysis_summary=analysis_summary,
        analyzed_at=datetime.now(UTC),
    )


@router.post("/student/{student_id}/verification-report", response_model=VerificationReportResponse)
async def generate_verification_report(
    student_id: str,
    course_id: str,
    request: VerificationReportCreate,
    db: DbSession,
    current_user: CurrentFaculty,
) -> VerificationReportResponse:
    """Generate a verification report for human assessment."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get student state
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == student_id,
            StudentState.course_id == course_id,
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="Student not enrolled")

    # Get concepts
    result = await db.execute(select(Concept).where(Concept.course_id == course_id))
    concepts = {c.id: c for c in result.scalars().all()}

    # Get interactions for excerpts
    result = await db.execute(
        select(Interaction)
        .where(
            Interaction.student_id == student_id,
            Interaction.course_id == course_id,
        )
        .order_by(Interaction.timestamp.desc())
        .limit(100)
    )
    interactions = list(result.scalars().all())

    # Build mastery estimates
    mastery_by_concept = []
    for concept_id, mastery_data in state.concept_mastery.items():
        concept = concepts.get(concept_id)
        mastery_by_concept.append(
            MasteryEstimate(
                concept_id=concept_id,
                concept_name=concept.name if concept else "Unknown",
                estimate=mastery_data.get("estimate", 0.0),
                confidence=mastery_data.get("confidence", 0.0),
                interaction_count=mastery_data.get("interactions", 0),
                last_updated=mastery_data.get("last_updated"),
            )
        )

    # Build concerns from gaming flags
    concerns = [
        GamingFlag(
            type=flag.get("type", "unknown"),
            severity=flag.get("severity", "low"),
            timestamp=flag.get("timestamp", datetime.now(UTC)),
            evidence=flag.get("evidence", ""),
            resolved=flag.get("resolved", False),
        )
        for flag in state.gaming_flags
        if not flag.get("resolved", False)
    ]

    # Generate verification questions
    # TODO: Use actual question generation logic
    recommended_questions = []
    for concept_id, mastery_data in state.concept_mastery.items():
        estimate = mastery_data.get("estimate", 0.0)
        if 0.4 <= estimate <= 0.7:  # Uncertain mastery
            concept = concepts.get(concept_id)
            if concept:
                recommended_questions.append(
                    VerificationQuestion(
                        concept_id=concept_id,
                        concept_name=concept.name,
                        question=f"Can you explain {concept.name} in your own words?",
                        rationale="Uncertain mastery level requires verification",
                        look_for="Clear explanation demonstrating understanding",
                        difficulty="medium",
                    )
                )

    recommended_questions = recommended_questions[: request.max_questions]

    # Select key excerpts
    key_excerpts = []
    if request.include_excerpts and interactions:
        # Find interactions with gaming signals
        for interaction in interactions[:10]:
            if interaction.gaming_signals:
                key_excerpts.append(
                    InteractionExcerpt(
                        type="gaming_flag",
                        concept_id=interaction.concept_id,
                        interactions=[
                            {
                                "student_message": interaction.student_message,
                                "tutor_response": interaction.tutor_response,
                                "timestamp": interaction.timestamp.isoformat(),
                            }
                        ],
                        note="Interaction flagged for potential gaming",
                        timestamp=interaction.timestamp,
                    )
                )

    # Build summary
    estimates = [m.estimate for m in mastery_by_concept]
    summary = {
        "total_interactions": state.engagement_metrics.get("total_interactions", 0),
        "total_time_minutes": state.engagement_metrics.get("total_time_seconds", 0) / 60,
        "concepts_completed": len(state.concepts_completed or []),
        "total_concepts": len(concepts),
        "overall_mastery": sum(estimates) / len(estimates) if estimates else 0.0,
        "gaming_flags_count": len(concerns),
    }

    # Create report
    report_data = {
        "summary": summary,
        "mastery_by_concept": [m.model_dump() for m in mastery_by_concept],
        "concerns": [c.model_dump() for c in concerns],
        "recommended_questions": [q.model_dump() for q in recommended_questions],
        "key_excerpts": [e.model_dump() for e in key_excerpts],
    }

    report = VerificationReport(
        student_id=student_id,
        course_id=course_id,
        report_data=report_data,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return VerificationReportResponse(
        id=report.id,
        student_id=student_id,
        course_id=course_id,
        generated_at=report.generated_at,
        verification_status=report.verification_status,
        verified_by=report.verified_by,
        verified_at=report.verified_at,
        verification_notes=report.verification_notes,
        summary=summary,
        mastery_by_concept=mastery_by_concept,
        concerns=concerns,
        recommended_questions=recommended_questions,
        key_excerpts=key_excerpts,
        assessment_scores=report.assessment_scores,
        overall_assessment=report.overall_assessment,
    )


@router.post("/verification/{report_id}/complete", response_model=VerificationReportResponse)
async def complete_verification(
    report_id: str,
    results: VerificationResults,
    db: DbSession,
    current_user: CurrentFaculty,
) -> VerificationReportResponse:
    """Record results from human verification."""
    result = await db.execute(
        select(VerificationReport)
        .where(VerificationReport.id == report_id)
        .options(selectinload(VerificationReport.course))
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update report
    report.verification_status = "completed"
    report.verified_by = current_user.id
    report.verified_at = datetime.now(UTC)
    report.verification_notes = results.verification_notes
    report.assessment_scores = results.assessment_scores
    report.overall_assessment = results.overall_assessment

    await db.flush()
    await db.refresh(report)

    # Get concepts for names
    result = await db.execute(select(Concept).where(Concept.course_id == report.course_id))
    {c.id: c for c in result.scalars().all()}

    # Rebuild response objects from report_data
    mastery_by_concept = [
        MasteryEstimate(**m) for m in report.report_data.get("mastery_by_concept", [])
    ]
    concerns = [GamingFlag(**c) for c in report.report_data.get("concerns", [])]
    recommended_questions = [
        VerificationQuestion(**q) for q in report.report_data.get("recommended_questions", [])
    ]
    key_excerpts = [InteractionExcerpt(**e) for e in report.report_data.get("key_excerpts", [])]

    return VerificationReportResponse(
        id=report.id,
        student_id=report.student_id,
        course_id=report.course_id,
        generated_at=report.generated_at,
        verification_status=report.verification_status,
        verified_by=report.verified_by,
        verified_at=report.verified_at,
        verification_notes=report.verification_notes,
        summary=report.report_data.get("summary", {}),
        mastery_by_concept=mastery_by_concept,
        concerns=concerns,
        recommended_questions=recommended_questions,
        key_excerpts=key_excerpts,
        assessment_scores=report.assessment_scores,
        overall_assessment=report.overall_assessment,
    )


@router.get("/course/{course_id}/reports")
async def list_verification_reports(
    course_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
    status_filter: str | None = None,
) -> list[dict]:
    """List verification reports for a course."""
    # Verify course ownership
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(VerificationReport).where(VerificationReport.course_id == course_id)

    if status_filter:
        query = query.where(VerificationReport.verification_status == status_filter)

    result = await db.execute(
        query.options(selectinload(VerificationReport.student)).order_by(
            VerificationReport.generated_at.desc()
        )
    )
    reports = result.scalars().all()

    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.full_name if r.student else None,
            "student_email": r.student.email if r.student else None,
            "generated_at": r.generated_at,
            "verification_status": r.verification_status,
            "overall_assessment": r.overall_assessment,
            "has_concerns": r.has_concerns,
        }
        for r in reports
    ]
