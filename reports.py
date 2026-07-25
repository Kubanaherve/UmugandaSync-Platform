"""
reports.py
Owner: Marvella (mmarvellio77)

Production reporting and analytics for UmugandaSync village leaders.

Layers
------
1. Helpers / validation
2. Data access (parameterized SQL via database.run_query)
3. Metric builders (pure-ish aggregations)
4. Console presentation
5. File exports
6. Interactive menu

Public entrypoint used by main.py: ``reports_menu()``.

Production checklist covered by this module:
    - Community / member / attendance / project / inventory reports
    - Overdue project highlighting
    - KPI snapshot for leaders
    - Timestamped exports under ``exports/`` (TXT and CSV)
    - None-safe aggregates for empty tables
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from typing import Any, Optional

import database
import helpers
import languages

logger = logging.getLogger(__name__)

EXPORT_DIR = os.environ.get("UMUGANDA_CSV_DIR", "exports")


# =============================================================================
# Exceptions
# =============================================================================
class ReportError(Exception):
    """Base error for the reports module."""


class ReportQueryError(ReportError):
    """Raised when a report query fails or returns unusable data."""


class ReportExportError(ReportError):
    """Raised when a report cannot be written to disk."""


# =============================================================================
# Helpers
# =============================================================================
def safe_num(value: Any) -> int | float:
    """
    Coerce None to 0 so empty-table aggregates never crash formatting.

    Parameters
    ----------
    value:
        Numeric aggregate or None.

    Returns
    -------
    int | float
    """
    if value is None:
        return 0
    return value


def safe_row(row: Optional[dict[str, Any]], key: str, default: Any = 0) -> Any:
    """
    Safely read a key from a possibly-None dictionary row.

    Parameters
    ----------
    row:
        Query result row or None when the DB layer fails.
    key:
        Column name.
    default:
        Fallback when row is None, key is missing, or value is None.
    """
    if row is None:
        return default
    value = row.get(key, default)
    if value is None:
        return default
    return value


def _query(sql: str, params: tuple = (), fetch: Optional[str] = "one") -> Any:
    """
    Run a parameterized report query.

    Returns
    -------
    Any
        Row, list of rows, or None.
    """
    try:
        return database.run_query(sql, params, fetch=fetch)
    except Exception as exc:  # pragma: no cover
        logger.exception("Report query failed")
        raise ReportQueryError(str(exc)) from exc


def _ensure_export_dir() -> str:
    """Create the export directory if needed and return its path."""
    path = EXPORT_DIR
    os.makedirs(path, exist_ok=True)
    return path


def make_export_filename(prefix: str, extension: str = "txt") -> str:
    """
    Build a timestamped export path under EXPORT_DIR.

    Parameters
    ----------
    prefix:
        Filename prefix, e.g. ``community_summary``.
    extension:
        File extension without dot (``txt`` or ``csv``).

    Returns
    -------
    str
        Path like ``exports/community_summary_20260725_230154.csv``.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = extension.lstrip(".") or "txt"
    return os.path.join(_ensure_export_dir(), f"{prefix}_{stamp}.{ext}")


def _export_filename(prefix: str) -> str:
    """Backward-compatible alias for text exports."""
    return make_export_filename(prefix, "txt")


def _write_export(filepath: str, lines: list[str]) -> str:
    """
    Write text lines to an export file.

    Returns
    -------
    str
        Absolute or relative filepath written.

    Raises
    ------
    ReportExportError
    """
    try:
        with open(filepath, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return filepath
    except OSError as exc:
        logger.exception("Export failed for %s", filepath)
        raise ReportExportError(f"Could not write {filepath}: {exc}") from exc


# =============================================================================
# Metric builders
# =============================================================================
def build_community_metrics() -> dict[str, Any]:
    """
    Collect high-level community KPIs for the dashboard-style summary.

    Returns
    -------
    dict
        Keys: total_members, active_members, total_projects, ongoing_projects,
        tool_types, available_tool_units, attendance_days, completion_rate
    """
    total_members = _query("SELECT COUNT(*) AS total FROM members", fetch="one")
    active_members = _query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one",
    )
    total_projects = _query("SELECT COUNT(*) AS total FROM projects", fetch="one")
    ongoing = _query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'",
        fetch="one",
    )
    completed = _query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Completed'",
        fetch="one",
    )
    total_tools = _query("SELECT COUNT(*) AS total FROM tools", fetch="one")
    available_tools = _query(
        "SELECT SUM(available_quantity) AS total FROM tools",
        fetch="one",
    )
    attendance_days = _query(
        "SELECT COUNT(DISTINCT attendance_date) AS total FROM attendance",
        fetch="one",
    )

    total_p = safe_row(total_projects, "total")
    completed_n = safe_row(completed, "total")
    completion_rate = (
        round(100.0 * float(completed_n) / float(total_p), 1) if total_p else 0.0
    )

    return {
        "total_members": safe_row(total_members, "total"),
        "active_members": safe_row(active_members, "total"),
        "total_projects": total_p,
        "ongoing_projects": safe_row(ongoing, "total"),
        "completed_projects": completed_n,
        "tool_types": safe_row(total_tools, "total"),
        "available_tool_units": safe_row(available_tools, "total"),
        "attendance_days": safe_row(attendance_days, "total"),
        "completion_rate": completion_rate,
    }


def build_member_breakdown() -> dict[str, list[dict[str, Any]]]:
    """Return member counts grouped by status and by village."""
    by_status = _query(
        """
        SELECT status, COUNT(*) AS total
        FROM members
        GROUP BY status
        ORDER BY status
        """,
        fetch="all",
    ) or []
    by_village = _query(
        """
        SELECT village, COUNT(*) AS total
        FROM members
        GROUP BY village
        ORDER BY total DESC
        """,
        fetch="all",
    ) or []
    return {"by_status": by_status, "by_village": by_village}
