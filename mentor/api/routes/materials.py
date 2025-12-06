"""Material upload and management routes."""

import os
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentFaculty, CurrentUser, DbSession
from mentor.config import settings
from mentor.models import Course, Material

router = APIRouter(prefix="/materials", tags=["materials"])

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}


class MaterialCreate(BaseModel):
    """Schema for creating material metadata."""

    title: str
    material_type: str
    concept_ids: list[str] = []


class MaterialResponse(BaseModel):
    """Schema for material response."""

    id: str
    course_id: str
    title: str
    material_type: str
    original_filename: str | None
    mime_type: str | None
    concept_ids: list[str]
    processing_status: str
    processing_error: str | None

    model_config = {"from_attributes": True}


class MaterialProcessingStatus(BaseModel):
    """Schema for material processing status."""

    id: str
    status: str
    error: str | None
    chunks_created: int = 0


@router.post(
    "/courses/{course_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    course_id: str,
    title: str,
    material_type: str,
    file: UploadFile = File(...),
    concept_ids: str = "",  # Comma-separated
    db: DbSession = None,
    current_user: CurrentFaculty = None,
) -> Material:
    """Upload a new material file."""
    # Verify course access
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB",
        )

    # Save file
    upload_dir = Path(settings.upload_dir) / course_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_ext = ALLOWED_MIME_TYPES[file.content_type]
    file_id = str(uuid4())
    file_path = upload_dir / f"{file_id}{file_ext}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Parse concept IDs
    parsed_concept_ids = [cid.strip() for cid in concept_ids.split(",") if cid.strip()]

    # Create material record
    material = Material(
        course_id=course_id,
        title=title,
        material_type=material_type,
        original_filename=file.filename,
        file_path=str(file_path),
        mime_type=file.content_type,
        concept_ids=parsed_concept_ids,
        processing_status="pending",
    )
    db.add(material)
    await db.flush()
    await db.refresh(material)

    # TODO: Trigger async processing task

    return material


@router.get("/courses/{course_id}/materials", response_model=list[MaterialResponse])
async def list_materials(
    course_id: str,
    db: DbSession,
    current_user: CurrentUser,
    material_type: str | None = None,
) -> list[Material]:
    """List materials in a course."""
    query = select(Material).where(Material.course_id == course_id)

    if material_type:
        query = query.where(Material.material_type == material_type)

    result = await db.execute(query.order_by(Material.created_at.desc()))
    return list(result.scalars().all())


@router.get(
    "/courses/{course_id}/materials/{material_id}",
    response_model=MaterialResponse,
)
async def get_material(
    course_id: str,
    material_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> Material:
    """Get a specific material."""
    result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.course_id == course_id,
        )
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    return material


@router.get(
    "/courses/{course_id}/materials/{material_id}/status",
    response_model=MaterialProcessingStatus,
)
async def get_material_status(
    course_id: str,
    material_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> MaterialProcessingStatus:
    """Get processing status of a material."""
    result = await db.execute(
        select(Material)
        .where(Material.id == material_id, Material.course_id == course_id)
        .options(selectinload(Material.chunks))
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    return MaterialProcessingStatus(
        id=material.id,
        status=material.processing_status,
        error=material.processing_error,
        chunks_created=len(material.chunks),
    )


@router.delete(
    "/courses/{course_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    course_id: str,
    material_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> None:
    """Delete a material."""
    result = await db.execute(
        select(Material)
        .where(Material.id == material_id, Material.course_id == course_id)
        .options(selectinload(Material.course))
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete file if exists
    if material.file_path and os.path.exists(material.file_path):
        os.remove(material.file_path)

    await db.delete(material)


@router.post(
    "/courses/{course_id}/materials/{material_id}/reprocess",
    response_model=MaterialProcessingStatus,
)
async def reprocess_material(
    course_id: str,
    material_id: str,
    db: DbSession,
    current_user: CurrentFaculty,
) -> MaterialProcessingStatus:
    """Trigger reprocessing of a material."""
    result = await db.execute(
        select(Material)
        .where(Material.id == material_id, Material.course_id == course_id)
        .options(selectinload(Material.course))
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.course.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Reset processing status
    material.processing_status = "pending"
    material.processing_error = None

    await db.flush()

    # TODO: Trigger async processing task

    return MaterialProcessingStatus(
        id=material.id,
        status=material.processing_status,
        error=material.processing_error,
        chunks_created=0,
    )
