import os
import uuid
import math
from typing import Any, Dict, Optional, List
from fastapi import UploadFile
from sqlalchemy.orm import Query
from datetime import datetime, timezone

def format_relative_time(dt: datetime) -> str:
    if not dt:
        return ""

    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    diff = now - dt
    seconds = int(diff.total_seconds())

    # If timestamp is in the future (due to timezone mismatch)
    if seconds < 0:
        seconds = abs(seconds)

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"

    days = hours // 24
    if days < 7:
        return f"{days}d"

    if dt.year == now.year:
        return dt.strftime("%b %d")

    return dt.strftime("%b %d %Y")

def apply_dynamic_filters(query: Query, model: Any, filters: Any, filter_map: Dict[str, Any]) -> Query:
    """
    Dynamically applies filters to a SQLAlchemy query based on a filter map.
    """
    for field, column in filter_map.items():
        value = getattr(filters, field, None)
        if value is not None:
            query = query.filter(column == value)
    return query

def build_pagination_meta(page: int, per_page: int, total_count: int) -> Dict[str, Any]:
    """
    Builds pagination metadata.
    """
    total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0
    return {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def save_upload_file(upload_file: UploadFile, destination_dir: str = "uploads") -> str:
    """
    Saves an uploaded file to the specified destination directory and returns the file path.
    """
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(destination_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())

    # Return the URL path (relative to the app root)
    return f"/{destination_dir}/{unique_filename}"


def delete_file(file_url: str) -> bool:
    """
    Deletes a file from the filesystem based on its URL path.
    """
    # Remove leading slash if present
    if file_url.startswith("/"):
        file_path = file_url[1:]
    else:
        file_path = file_url

    # Normalize path for current OS
    file_path = os.path.normpath(file_path)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
