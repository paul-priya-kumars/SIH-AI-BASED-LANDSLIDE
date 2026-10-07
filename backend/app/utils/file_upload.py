import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException
from ..config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

def validate_image_file(file: UploadFile) -> None:
    """Validates that the uploaded file is an acceptable image format and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: JPG, JPEG, PNG, WEBP."
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME content type '{file.content_type}'. Must be an image (JPEG, PNG, WEBP)."
        )

async def save_uploaded_image(file: UploadFile) -> Tuple[str, str]:
    """
    Saves an uploaded image to the designated uploads directory.
    Returns:
        (relative_storage_path, relative_url_path)
    """
    validate_image_file(file)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    target_filepath = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Read and enforce max size limit
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    with open(target_filepath, "wb") as f:
        f.write(content)

    relative_storage_path = os.path.join("uploads", unique_filename).replace("\\", "/")
    relative_url_path = f"/uploads/{unique_filename}"

    return relative_storage_path, relative_url_path