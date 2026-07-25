"""
projects.py
Owner: Sonia — Project Management module for UmugandaSync.

Clean architecture (single module, layered sections):
    1. Exceptions & constants
    2. Validation
    3. Data access (repository)
    4. Domain services (progress, deadlines, overdue)
    5. Presentation (display, alerts, reports)
    6. Interactive UI handlers + menu
    7. Public APIs consumed by notifications / dashboard

Features:
    - Add project
    - Edit project
    - Complete project
    - Progress tracking
    - Deadline monitoring
    - Overdue alerts
    - Project reports

Other modules should call:
    project_menu(), list_overdue_project_names(), count_overdue_projects()
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

import database
import helpers
import languages

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_STATUSES: tuple[str, ...] = ("Pending", "Ongoing", "Completed", "Cancelled")
ACTIVE_STATUSES: tuple[str, ...] = ("Pending", "Ongoing")
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 100
MAX_LOCATION_LENGTH: int = 100
MAX_DESCRIPTION_LENGTH: int = 2000
DEADLINE_WARN_DAYS: int = 7  # nearing deadline window


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class ProjectError(Exception):
    """Base error for project management failures."""


class ProjectValidationError(ProjectError):
    """Raised when project input fails validation."""


class ProjectNotFoundError(ProjectError):
    """Raised when a project ID does not exist."""


class ProjectDataError(ProjectError):
    """Raised when a database operation fails unexpectedly."""


# ---------------------------------------------------------------------------
# Validation layer
# ---------------------------------------------------------------------------
def validate_project_name(name: Optional[str]) -> str:
    """
    Validate and clean a project name.

    Parameters
    ----------
    name:
        Raw project name.

    Returns
    -------
    str
        Stripped project name.

    Raises
    ------
    ProjectValidationError
        If name is empty or outside length bounds.
    """
    if name is None:
        raise ProjectValidationError("Project name is required.")
    cleaned = str(name).strip()
    if len(cleaned) < MIN_NAME_LENGTH:
        raise ProjectValidationError(
            f"Project name must be at least {MIN_NAME_LENGTH} characters."
        )
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ProjectValidationError(
            f"Project name must be at most {MAX_NAME_LENGTH} characters."
        )
    return cleaned


def validate_location(location: Optional[str]) -> str:
    """
    Validate project location.

    Raises
    ------
    ProjectValidationError
        If location is blank or too long.
    """
    if location is None or str(location).strip() == "":
        raise ProjectValidationError("Location is required.")
    cleaned = str(location).strip()
    if len(cleaned) > MAX_LOCATION_LENGTH:
        raise ProjectValidationError("Location is too long.")
    return cleaned


def validate_description(description: Optional[str]) -> Optional[str]:
    """
    Clean optional description; empty becomes None.

    Raises
    ------
    ProjectValidationError
        If description exceeds max length.
    """
    if description is None:
        return None
    cleaned = str(description).strip()
    if cleaned == "":
        return None
    if len(cleaned) > MAX_DESCRIPTION_LENGTH:
        raise ProjectValidationError("Description is too long.")
    return cleaned


def validate_percent_complete(percent: Any) -> int:
    """
    Validate progress percentage is an int in 0..100.

    Raises
    ------
    ProjectValidationError
    """
    try:
        value = int(percent)
    except (TypeError, ValueError) as exc:
        raise ProjectValidationError("Progress must be an integer.") from exc
    if value < 0 or value > 100:
        raise ProjectValidationError("Progress must be between 0 and 100.")
    return value


def validate_status(status: Optional[str]) -> str:
    """
    Validate project status against allowed values.

    Raises
    ------
    ProjectValidationError
    """
    if status is None or str(status).strip() not in VALID_STATUSES:
        raise ProjectValidationError(
            "Status must be one of: " + ", ".join(VALID_STATUSES)
        )
    return str(status).strip()


def validate_date_string(value: Optional[str], *, field_name: str = "date") -> str:
    """
    Validate YYYY-MM-DD date string.

    Returns
    -------
    str
        Normalized date string.

    Raises
    ------
    ProjectValidationError
    """
    if value is None or str(value).strip() == "":
        raise ProjectValidationError(f"{field_name} is required.")
    text = str(value).strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ProjectValidationError(
            f"{field_name} must use YYYY-MM-DD format."
        ) from exc
    return text


def validate_date_range(start_date: str, end_date: str) -> None:
    """
    Ensure expected end date is on or after start date.

    Raises
    ------
    ProjectValidationError
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if end < start:
        raise ProjectValidationError(
            "Expected end date cannot be before start date."
        )


def validate_leader_id(leader_id: Any) -> int:
    """
    Validate leader member id is a positive integer.

    Raises
    ------
    ProjectValidationError
    """
    try:
        value = int(leader_id)
    except (TypeError, ValueError) as exc:
        raise ProjectValidationError("Leader member ID must be an integer.") from exc
    if value <= 0:
        raise ProjectValidationError("Leader member ID must be positive.")
    return value


def derive_status_from_progress(current_status: str, percent: int) -> str:
    """
    Derive a sensible status when progress changes.

    Rules
    -----
    - 100% => Completed
    - >0 and Pending => Ongoing
    - otherwise keep current (unless Completed and percent < 100 => Ongoing)
    """
    if percent >= 100:
        return "Completed"
    if current_status == "Cancelled":
        return "Cancelled"
    if current_status == "Completed" and percent < 100:
        return "Ongoing"
    if percent > 0 and current_status == "Pending":
        return "Ongoing"
    return current_status


# ---------------------------------------------------------------------------
# Data access layer (repository)
# ---------------------------------------------------------------------------
def _query(
    sql: str,
    params: tuple = (),
    fetch: Optional[str] = None,
) -> Any:
    """
    Run a parameterized query via database.run_query.

    Returns
    -------
    Any
        Row, list of rows, lastrowid, or None.

    Raises
    ------
    ProjectDataError
        When the database layer returns None for a write that must succeed,
        or when an unexpected exception occurs.
    """
    try:
        return database.run_query(sql, params, fetch=fetch)
    except Exception as exc:  # pragma: no cover - driver-specific
        logger.exception("Project query failed")
        raise ProjectDataError(f"Database query failed: {exc}") from exc


def member_exists(member_id: int) -> bool:
    """Return True if member_id exists in members."""
    row = _query(
        "SELECT member_id FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one",
    )
    return row is not None


def get_project_by_id(project_id: int) -> Optional[dict[str, Any]]:
    """
    Fetch one project with leader name fields.

    Parameters
    ----------
    project_id:
        Primary key.

    Returns
    -------
    dict | None
    """
    return _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.project_id = %s
        """,
        (project_id,),
        fetch="one",
    )


def require_project(project_id: int) -> dict[str, Any]:
    """
    Fetch a project or raise ProjectNotFoundError.

    Raises
    ------
    ProjectNotFoundError
    """
    project = get_project_by_id(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project {project_id} not found.")
    return project


def fetch_all_projects() -> list[dict[str, Any]]:
    """Return all projects with leader names, newest start first."""
    rows = _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        ORDER BY p.start_date DESC
        """,
        fetch="all",
    )
    return rows or []


def fetch_projects_by_status(status: str) -> list[dict[str, Any]]:
    """Return projects filtered by status."""
    status = validate_status(status)
    rows = _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.status = %s
        ORDER BY p.start_date DESC
        """,
        (status,),
        fetch="all",
    )
    return rows or []


def fetch_overdue_projects(today: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Return active projects past their expected end date.

    Parameters
    ----------
    today:
        YYYY-MM-DD reference date; defaults to helpers.today_string().
    """
    if today is None:
        today = helpers.today_string()
    rows = _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.status IN ('Pending', 'Ongoing')
          AND p.expected_end_date < %s
        ORDER BY p.expected_end_date
        """,
        (today,),
        fetch="all",
    )
    return rows or []


def fetch_projects_nearing_deadline(
    today: Optional[str] = None,
    within_days: int = DEADLINE_WARN_DAYS,
) -> list[dict[str, Any]]:
    """
    Return active projects due within ``within_days`` (inclusive), not overdue.
    """
    if today is None:
        today = helpers.today_string()
    rows = _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.status IN ('Pending', 'Ongoing')
          AND p.expected_end_date >= %s
          AND p.expected_end_date <= DATE_ADD(%s, INTERVAL %s DAY)
        ORDER BY p.expected_end_date
        """,
        (today, today, within_days),
        fetch="all",
    )
    return rows or []


def search_projects_data(term: str) -> list[dict[str, Any]]:
    """Search projects by name or location (case-insensitive LIKE)."""
    cleaned = term.strip()
    if cleaned == "":
        raise ProjectValidationError("Search term cannot be empty.")
    like = f"%{cleaned}%"
    rows = _query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.project_name LIKE %s OR p.location LIKE %s
        ORDER BY p.project_name
        """,
        (like, like),
        fetch="all",
    )
    return rows or []
