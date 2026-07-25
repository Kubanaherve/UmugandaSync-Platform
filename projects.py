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


def insert_project(
    *,
    project_name: str,
    description: Optional[str],
    location: str,
    leader_member_id: int,
    start_date: str,
    expected_end_date: str,
    status: str = "Pending",
    percent_complete: int = 0,
) -> int:
    """
    Insert a project row.

    Returns
    -------
    int
        New project_id.

    Raises
    ------
    ProjectDataError
        If insert fails.
    """
    result = _query(
        """
        INSERT INTO projects
            (project_name, description, location, leader_member_id,
             start_date, expected_end_date, status, percent_complete)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            project_name,
            description,
            location,
            leader_member_id,
            start_date,
            expected_end_date,
            status,
            percent_complete,
        ),
    )
    if result is None:
        raise ProjectDataError("Failed to insert project.")
    return int(result)


def update_project_fields(project_id: int, fields: dict[str, Any]) -> None:
    """
    Update selected columns for a project using parameterized SQL.

    Raises
    ------
    ProjectValidationError
        If fields is empty.
    ProjectDataError
        If update fails.
    """
    if not fields:
        raise ProjectValidationError("No fields provided to update.")
    # Column names are controlled by callers (internal), values are bound.
    assignments = ", ".join(f"{column} = %s" for column in fields)
    params = tuple(fields.values()) + (project_id,)
    result = _query(
        f"UPDATE projects SET {assignments} WHERE project_id = %s",
        params,
    )
    if result is None:
        raise ProjectDataError(f"Failed to update project {project_id}.")


def delete_project_by_id(project_id: int) -> None:
    """
    Delete a project by id.

    Raises
    ------
    ProjectDataError
    """
    result = _query("DELETE FROM projects WHERE project_id = %s", (project_id,))
    if result is None:
        raise ProjectDataError(f"Failed to delete project {project_id}.")


def fetch_status_counts() -> dict[str, int]:
    """Return counts keyed by status for reports."""
    rows = _query(
        """
        SELECT status, COUNT(*) AS total
        FROM projects
        GROUP BY status
        """,
        fetch="all",
    ) or []
    counts = {status: 0 for status in VALID_STATUSES}
    for row in rows:
        counts[row["status"]] = int(row["total"])
    return counts


def fetch_average_completion() -> float:
    """Return average percent_complete across all projects."""
    row = _query(
        "SELECT AVG(percent_complete) AS avg_pct FROM projects",
        fetch="one",
    )
    if row is None or row["avg_pct"] is None:
        return 0.0
    return float(row["avg_pct"])


# ---------------------------------------------------------------------------
# Domain services — deadlines, progress, overdue
# ---------------------------------------------------------------------------
def _parse_date(value: Any) -> date:
    """Parse a DB date / string into a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def days_until_deadline(expected_end_date: Any, today: Optional[date] = None) -> int:
    """
    Days remaining until deadline (negative if overdue).

    Parameters
    ----------
    expected_end_date:
        Project deadline.
    today:
        Reference day; defaults to local today.
    """
    if today is None:
        today = date.today()
    return (_parse_date(expected_end_date) - today).days


def is_project_overdue(project: dict[str, Any], today: Optional[date] = None) -> bool:
    """True when project is active and past expected_end_date."""
    if project.get("status") not in ACTIVE_STATUSES:
        return False
    return days_until_deadline(project["expected_end_date"], today) < 0


def deadline_label(project: dict[str, Any], today: Optional[date] = None) -> str:
    """
    Human-readable deadline urgency label.

    Returns
    -------
    str
        One of: OVERDUE, DUE_TODAY, DUE_SOON, ON_TRACK, N/A
    """
    if project.get("status") in ("Completed", "Cancelled"):
        return "N/A"
    remaining = days_until_deadline(project["expected_end_date"], today)
    if remaining < 0:
        return "OVERDUE"
    if remaining == 0:
        return "DUE_TODAY"
    if remaining <= DEADLINE_WARN_DAYS:
        return "DUE_SOON"
    return "ON_TRACK"


def apply_progress(project_id: int, percent: int) -> dict[str, Any]:
    """
    Update progress and derived status for a project.

    Returns
    -------
    dict
        Updated project row.
    """
    percent = validate_percent_complete(percent)
    project = require_project(project_id)
    new_status = derive_status_from_progress(project["status"], percent)
    update_project_fields(
        project_id,
        {"percent_complete": percent, "status": new_status},
    )
    logger.info(
        "Project %s progress set to %s%% (status=%s)",
        project_id,
        percent,
        new_status,
    )
    return require_project(project_id)


def complete_project(project_id: int) -> dict[str, Any]:
    """
    Mark a project completed at 100%.

    Returns
    -------
    dict
        Updated project.
    """
    require_project(project_id)
    update_project_fields(
        project_id,
        {"status": "Completed", "percent_complete": 100},
    )
    logger.info("Project %s marked completed", project_id)
    return require_project(project_id)


def create_project_record(
    *,
    project_name: str,
    description: Optional[str],
    location: str,
    leader_member_id: int,
    start_date: str,
    expected_end_date: str,
) -> int:
    """
    Validate inputs and insert a new project.

    Returns
    -------
    int
        New project_id.

    Raises
    ------
    ProjectValidationError
        On invalid input or missing leader.
    """
    name = validate_project_name(project_name)
    loc = validate_location(location)
    desc = validate_description(description)
    leader = validate_leader_id(leader_member_id)
    start = validate_date_string(start_date, field_name="Start date")
    end = validate_date_string(expected_end_date, field_name="Expected end date")
    validate_date_range(start, end)

    if not member_exists(leader):
        raise ProjectValidationError("Leader member was not found.")

    new_id = insert_project(
        project_name=name,
        description=desc,
        location=loc,
        leader_member_id=leader,
        start_date=start,
        expected_end_date=end,
        status="Pending",
        percent_complete=0,
    )
    logger.info("Created project %s (%s)", new_id, name)
    return new_id


def edit_project_record(
    project_id: int,
    *,
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    leader_member_id: Optional[int] = None,
    start_date: Optional[str] = None,
    expected_end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """
    Edit mutable project fields (partial update).

    Only provided (not None) fields are changed, except description which
    may be cleared with an empty string.

    Returns
    -------
    dict
        Updated project.
    """
    project = require_project(project_id)
    fields: dict[str, Any] = {}

    if project_name is not None:
        fields["project_name"] = validate_project_name(project_name)
    if description is not None:
        fields["description"] = validate_description(description)
    if location is not None:
        fields["location"] = validate_location(location)
    if leader_member_id is not None:
        leader = validate_leader_id(leader_member_id)
        if not member_exists(leader):
            raise ProjectValidationError("Leader member was not found.")
        fields["leader_member_id"] = leader
    if status is not None:
        fields["status"] = validate_status(status)

    new_start = (
        validate_date_string(start_date, field_name="Start date")
        if start_date is not None
        else str(project["start_date"])
    )
    new_end = (
        validate_date_string(expected_end_date, field_name="Expected end date")
        if expected_end_date is not None
        else str(project["expected_end_date"])
    )
    if start_date is not None:
        fields["start_date"] = new_start
    if expected_end_date is not None:
        fields["expected_end_date"] = new_end
    validate_date_range(
        fields.get("start_date", new_start),
        fields.get("expected_end_date", new_end),
    )

    if not fields:
        raise ProjectValidationError("No changes provided.")

    update_project_fields(project_id, fields)
    logger.info("Edited project %s fields=%s", project_id, list(fields))
    return require_project(project_id)


# ---------------------------------------------------------------------------
# Presentation — display, alerts, reports
# ---------------------------------------------------------------------------
def _leader_display(row: dict[str, Any]) -> str:
    """Format leader full name for console output."""
    leader = f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
    if leader == "":
        return languages.t("no_leader")
    return leader


def _display_projects(rows: Optional[list[dict[str, Any]]]) -> None:
    """
    Print a compact project table with deadline urgency.

    Parameters
    ----------
    rows:
        Project dictionaries (may be None/empty).
    """
    if not rows:
        print(languages.t("no_projects"))
        return

    today = date.today()
    for row in rows:
        urgency = deadline_label(row, today)
        remaining = days_until_deadline(row["expected_end_date"], today)
        if urgency == "OVERDUE":
            due_note = f"OVERDUE {-remaining}d"
        elif urgency == "N/A":
            due_note = urgency
        else:
            due_note = f"{remaining}d left"

        print(
            "P#" + str(row["project_id"]).rjust(3),
            str(row["project_name"]).ljust(28)[:28],
            "|",
            str(row["status"]).ljust(10),
            "|",
            str(row["percent_complete"]).rjust(3) + "%",
            "|",
            languages.t("due"),
            str(row["expected_end_date"]),
            f"({due_note})",
            "|",
            languages.t("leader") + ":",
            _leader_display(row),
        )
    print()
    print(languages.t("total") + ":", len(rows))


def show_overdue_alerts() -> int:
    """
    Print overdue project alerts.

    Returns
    -------
    int
        Number of overdue projects alerted.
    """
    helpers.print_line(
        languages.t("overdue_alerts_title", fallback="OVERDUE PROJECT ALERTS")
    )
    rows = fetch_overdue_projects()
    if not rows:
        helpers.success(
            languages.t("no_overdue_projects", fallback="No overdue projects.")
        )
        return 0

    helpers.warning(
        languages.t(
            "overdue_alert_count",
            fallback=f"{len(rows)} project(s) are overdue.",
        ).replace("{n}", str(len(rows)))
    )
    for row in rows:
        days_late = -days_until_deadline(row["expected_end_date"])
        print(
            f"  ! P#{row['project_id']} {row['project_name']} "
            f"— due {row['expected_end_date']} ({days_late} day(s) late) "
            f"— {row['percent_complete']}% — leader: {_leader_display(row)}"
        )
    return len(rows)


def show_deadline_monitor() -> None:
    """Show overdue + nearing-deadline projects for monitoring."""
    helpers.print_line(
        languages.t("deadline_monitor_title", fallback="DEADLINE MONITORING")
    )

    overdue = fetch_overdue_projects()
    soon = fetch_projects_nearing_deadline()

    print(languages.t("overdue_section", fallback="-- Overdue --"))
    _display_projects(overdue)

    print(
        languages.t(
            "due_soon_section",
            fallback=f"-- Due within {DEADLINE_WARN_DAYS} days --",
        )
    )
    _display_projects(soon)


def build_project_report() -> dict[str, Any]:
    """
    Build aggregated project report metrics.

    Returns
    -------
    dict
        Keys: total, by_status, average_completion, overdue_count,
        nearing_deadline_count, completion_rate
    """
    by_status = fetch_status_counts()
    total = sum(by_status.values())
    completed = by_status.get("Completed", 0)
    overdue_count = len(fetch_overdue_projects())
    nearing = len(fetch_projects_nearing_deadline())
    avg_pct = fetch_average_completion()
    completion_rate = (completed / total * 100.0) if total else 0.0
    return {
        "total": total,
        "by_status": by_status,
        "average_completion": avg_pct,
        "overdue_count": overdue_count,
        "nearing_deadline_count": nearing,
        "completion_rate": completion_rate,
    }


def show_project_report() -> None:
    """Print a full project management report to the console."""
    helpers.print_line(
        languages.t("project_report_title", fallback="PROJECT REPORT")
    )
    report = build_project_report()

    print(languages.t("total") + ":", report["total"])
    print(
        languages.t("project_completion_rate"),
        f"{report['completion_rate']:.1f}%",
    )
    print(
        languages.t("avg_progress", fallback="Average progress:"),
        f"{report['average_completion']:.1f}%",
    )
    print(
        languages.t("overdue_count_label", fallback="Overdue projects:"),
        report["overdue_count"],
    )
    print(
        languages.t("due_soon_count_label", fallback="Nearing deadline:"),
        report["nearing_deadline_count"],
    )
    print()
    print(languages.t("status_breakdown", fallback="Status breakdown:"))
    for status in VALID_STATUSES:
        count = report["by_status"].get(status, 0)
        print(f"  {status.ljust(12)}: {count}")
    print()


# ---------------------------------------------------------------------------
# Interactive UI handlers
# ---------------------------------------------------------------------------
def register_project() -> None:
    """Interactive flow: add a new community project."""
    helpers.print_line(languages.t("p1"))
    try:
        project_name = helpers.get_non_empty(languages.t("project_name_prompt"))
        description = input(languages.t("project_desc_prompt")).strip()
        location = helpers.get_non_empty(languages.t("project_location_prompt"))
        leader = helpers.get_positive_int(languages.t("project_leader_prompt"))
        start_date = helpers.get_date(languages.t("project_start_prompt"))
        end_date = helpers.get_date(languages.t("project_end_prompt"))

        new_id = create_project_record(
            project_name=project_name,
            description=description,
            location=location,
            leader_member_id=leader,
            start_date=start_date,
            expected_end_date=end_date,
        )
        helpers.success(languages.t("project_added") + f" (ID: {new_id})")
    except ProjectValidationError as exc:
        helpers.error(str(exc))
    except ProjectDataError as exc:
        helpers.error(languages.t("project_add_failed") + f" ({exc})")
    helpers.pause()


def edit_project() -> None:
    """Interactive flow: edit an existing project's details."""
    helpers.print_line(
        languages.t("edit_project_title", fallback="EDIT PROJECT")
    )
    try:
        project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
        project = require_project(project_id)

        print(languages.t("current_values") + ":")
        print(
            f"  {project['project_name']} | {project['status']} | "
            f"{project['percent_complete']}% | "
            f"{languages.t('due')} {project['expected_end_date']}"
        )
        print(
            languages.t(
                "edit_blank_keeps",
                fallback="(Press Enter to keep a value unchanged)",
            )
        )

        name_in = input(languages.t("project_name_prompt")).strip()
        desc_in = input(languages.t("project_desc_prompt"))
        loc_in = input(languages.t("project_location_prompt")).strip()
        leader_in = input(languages.t("project_leader_prompt")).strip()
        start_in = input(
            languages.t("project_start_prompt") + " (YYYY-MM-DD): "
        ).strip()
        end_in = input(
            languages.t("project_end_prompt") + " (YYYY-MM-DD): "
        ).strip()
        status_in = input(
            languages.t("status_prompt", fallback="Status: ")
        ).strip()

        updated = edit_project_record(
            project_id,
            project_name=name_in or None,
            description=desc_in.strip() if desc_in.strip() else None,
            location=loc_in or None,
            leader_member_id=int(leader_in) if leader_in else None,
            start_date=start_in or None,
            expected_end_date=end_in or None,
            status=status_in or None,
        )
        helpers.success(
            languages.t("project_updated")
            + f" (P#{updated['project_id']})"
        )
    except ProjectNotFoundError:
        helpers.error(languages.t("project_not_found"))
    except (ProjectValidationError, ValueError) as exc:
        helpers.error(str(exc))
    except ProjectDataError as exc:
        helpers.error(languages.t("project_update_failed") + f" ({exc})")
    helpers.pause()


def view_all_projects() -> None:
    """Interactive: list every project."""
    helpers.print_line(languages.t("p2"))
    _display_projects(fetch_all_projects())
    helpers.pause()


def view_projects_by_status(status: str) -> None:
    """Interactive: list projects filtered by status."""
    label = {"Ongoing": languages.t("p3"), "Completed": languages.t("p4")}
    helpers.print_line(label.get(status, status))
    try:
        _display_projects(fetch_projects_by_status(status))
    except ProjectValidationError as exc:
        helpers.error(str(exc))
    helpers.pause()


def view_overdue_projects() -> None:
    """Interactive: list overdue projects (deadline monitoring entry)."""
    helpers.print_line(languages.t("p5"))
    _display_projects(fetch_overdue_projects())
    helpers.pause()


def search_projects() -> None:
    """Interactive: search projects by name or location."""
    helpers.print_line(languages.t("p6"))
    try:
        term = helpers.get_non_empty(languages.t("search_term_prompt"))
        _display_projects(search_projects_data(term))
    except ProjectValidationError as exc:
        helpers.error(str(exc))
    helpers.pause()


def update_project_progress() -> None:
    """Interactive: update percent complete / progress tracking."""
    helpers.print_line(languages.t("p7"))
    try:
        project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
        project = require_project(project_id)

        print(languages.t("current_values") + ":")
        print(
            "  ",
            project["project_name"],
            "|",
            project["status"],
            "|",
            str(project["percent_complete"]) + "%",
            "|",
            languages.t("due"),
            project["expected_end_date"],
            "|",
            deadline_label(project),
        )

        percent = helpers.get_int_in_range(
            languages.t("progress_prompt") + " (0-100): ", 0, 100
        )
        updated = apply_progress(project_id, percent)
        helpers.success(
            languages.t("project_updated")
            + f" → {updated['percent_complete']}% ({updated['status']})"
        )
    except ProjectNotFoundError:
        helpers.error(languages.t("project_not_found"))
    except ProjectValidationError as exc:
        helpers.error(str(exc))
    except ProjectDataError as exc:
        helpers.error(languages.t("project_update_failed") + f" ({exc})")
    helpers.pause()


def mark_project_completed() -> None:
    """Interactive: mark a project as completed."""
    helpers.print_line(languages.t("p8"))
    try:
        project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
        project = require_project(project_id)
        print(languages.t("mark_complete") + ":", project["project_name"])
        if helpers.confirm(languages.t("are_you_sure")):
            complete_project(project_id)
            helpers.success(languages.t("project_completed"))
    except ProjectNotFoundError:
        helpers.error(languages.t("project_not_found"))
    except ProjectDataError:
        helpers.error(languages.t("project_complete_failed"))
    helpers.pause()


def delete_project() -> None:
    """Interactive: delete a project after confirmation."""
    helpers.print_line(languages.t("p9"))
    try:
        project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
        project = require_project(project_id)
        print(languages.t("confirm_delete") + ":", project["project_name"])
        if helpers.confirm(languages.t("are_you_sure")):
            delete_project_by_id(project_id)
            helpers.success(languages.t("project_deleted"))
    except ProjectNotFoundError:
        helpers.error(languages.t("project_not_found"))
    except ProjectDataError:
        helpers.error(languages.t("project_delete_failed"))
    helpers.pause()


def project_reports_menu() -> None:
    """Interactive: show project reports and optional alert summary."""
    show_project_report()
    print()
    show_overdue_alerts()
    helpers.pause()


def project_menu() -> None:
    """
    Main project management menu.

    Options
    -------
    1 Add project
    2 View all
    3 Ongoing
    4 Completed
    5 Overdue list
    6 Search
    7 Progress tracking
    8 Complete project
    9 Delete project
    10 Edit project
    11 Deadline monitoring
    12 Reports & overdue alerts
    0 Back
    """
    running = True
    while running:
        helpers.print_line(languages.t("project_menu"))
        print(languages.t("p1"))
        print(languages.t("p2"))
        print(languages.t("p3"))
        print(languages.t("p4"))
        print(languages.t("p5"))
        print(languages.t("p6"))
        print(languages.t("p7"))
        print(languages.t("p8"))
        print(languages.t("p9"))
        print("10. " + languages.t("edit_project_title", fallback="Edit project"))
        print(
            "11. "
            + languages.t("deadline_monitor_title", fallback="Deadline monitoring")
        )
        print(
            "12. "
            + languages.t("project_report_title", fallback="Project reports & alerts")
        )
        print(languages.t("p0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            register_project()
        elif choice == "2":
            view_all_projects()
        elif choice == "3":
            view_projects_by_status("Ongoing")
        elif choice == "4":
            view_projects_by_status("Completed")
        elif choice == "5":
            view_overdue_projects()
        elif choice == "6":
            search_projects()
        elif choice == "7":
            update_project_progress()
        elif choice == "8":
            mark_project_completed()
        elif choice == "9":
            delete_project()
        elif choice == "10":
            edit_project()
        elif choice == "11":
            show_deadline_monitor()
            helpers.pause()
        elif choice == "12":
            project_reports_menu()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


# ---------------------------------------------------------------------------
# Public APIs for notifications / dashboard (backward compatible)
# ---------------------------------------------------------------------------
def count_overdue_projects() -> int:
    """
    Count active overdue projects.

    Returns
    -------
    int
    """
    today = helpers.today_string()
    row = _query(
        """
        SELECT COUNT(*) AS total FROM projects
        WHERE status IN ('Pending', 'Ongoing')
          AND expected_end_date < %s
        """,
        (today,),
        fetch="one",
    )
    if row is None:
        return 0
    return int(row["total"])


def list_overdue_project_names() -> list[str]:
    """
    Return overdue project names for the notification center.

    Returns
    -------
    list[str]
    """
    rows = fetch_overdue_projects()
    return [str(r["project_name"]) for r in rows]


__all__ = [
    "project_menu",
    "register_project",
    "edit_project",
    "view_all_projects",
    "view_projects_by_status",
    "view_overdue_projects",
    "search_projects",
    "update_project_progress",
    "mark_project_completed",
    "delete_project",
    "show_deadline_monitor",
    "show_overdue_alerts",
    "show_project_report",
    "build_project_report",
    "count_overdue_projects",
    "list_overdue_project_names",
    "create_project_record",
    "edit_project_record",
    "apply_progress",
    "complete_project",
    "ProjectError",
    "ProjectValidationError",
    "ProjectNotFoundError",
    "ProjectDataError",
]
