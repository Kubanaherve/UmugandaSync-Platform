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
from helpers import ExitRequested

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


def build_attendance_summary() -> dict[str, Any]:
    """Return attendance status counts and overall present/late rate."""
    rows = _query(
        """
        SELECT status, COUNT(*) AS total
        FROM attendance
        GROUP BY status
        ORDER BY total DESC
        """,
        fetch="all",
    ) or []
    avg_row = _query(
        """
        SELECT
          ROUND(
            100 * SUM(CASE WHEN status IN ('Present','Late') THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 1
          ) AS avg_present_pct
        FROM attendance
        """,
        fetch="one",
    )
    return {
        "by_status": rows,
        "avg_present_pct": None if avg_row is None else avg_row.get("avg_present_pct"),
    }


def build_most_active_members(limit: int = 10) -> list[dict[str, Any]]:
    """Top members by Present/Late attendance count."""
    if limit < 1:
        limit = 10
    return _query(
        """
        SELECT m.national_id, m.first_name, m.last_name, m.village,
               COUNT(*) AS active_count
        FROM attendance a
        JOIN members m ON a.member_id = m.national_id
        WHERE a.status IN ('Present', 'Late')
        GROUP BY m.national_id, m.first_name, m.last_name, m.village
        ORDER BY active_count DESC
        LIMIT %s
        """,
        (limit,),
        fetch="all",
    ) or []


def build_poor_attendance(min_absents: int = 2) -> list[dict[str, Any]]:
    """Members with at least ``min_absents`` Absent records."""
    if min_absents < 1:
        min_absents = 2
    return _query(
        """
        SELECT m.national_id, m.first_name, m.last_name, m.phone,
               COUNT(*) AS absent_count
        FROM attendance a
        JOIN members m ON a.member_id = m.national_id
        WHERE a.status = 'Absent'
        GROUP BY m.national_id, m.first_name, m.last_name, m.phone
        HAVING COUNT(*) >= %s
        ORDER BY absent_count DESC
        """,
        (min_absents,),
        fetch="all",
    ) or []


def build_project_summary() -> dict[str, Any]:
    """Project counts/avg progress by status plus incomplete list."""
    by_status = _query(
        """
        SELECT status, COUNT(*) AS total,
               ROUND(AVG(percent_complete), 1) AS avg_progress
        FROM projects
        GROUP BY status
        ORDER BY status
        """,
        fetch="all",
    ) or []
    incomplete = _query(
        """
        SELECT project_name, status, percent_complete, expected_end_date
        FROM projects
        WHERE status IN ('Pending', 'Ongoing')
        ORDER BY expected_end_date
        """,
        fetch="all",
    ) or []
    overdue = _query(
        """
        SELECT project_name, status, percent_complete, expected_end_date
        FROM projects
        WHERE status IN ('Pending', 'Ongoing')
          AND expected_end_date < CURDATE()
        ORDER BY expected_end_date
        """,
        fetch="all",
    ) or []
    return {
        "by_status": by_status,
        "incomplete": incomplete,
        "overdue": overdue,
    }


def build_inventory_summary() -> dict[str, Any]:
    """Tool inventory totals, condition, low stock, and open borrows."""
    totals = _query(
        """
        SELECT
          COUNT(*) AS tool_types,
          SUM(total_quantity) AS total_units,
          SUM(available_quantity) AS available_units
        FROM tools
        """,
        fetch="one",
    ) or {}
    by_cond = _query(
        """
        SELECT condition_status, COUNT(*) AS total
        FROM tools
        GROUP BY condition_status
        """,
        fetch="all",
    ) or []
    low = _query(
        """
        SELECT tool_name, available_quantity, low_stock_limit
        FROM tools
        WHERE available_quantity <= low_stock_limit
        ORDER BY available_quantity
        """,
        fetch="all",
    ) or []
    borrowed = _query(
        """
        SELECT t.tool_name, m.first_name, m.last_name, b.quantity, b.borrow_date
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        JOIN members m ON b.member_id = m.national_id
        WHERE b.status = 'Borrowed'
        ORDER BY b.borrow_date
        """,
        fetch="all",
    ) or []
    return {
        "totals": totals,
        "by_condition": by_cond,
        "low_stock": low,
        "borrowed": borrowed,
    }


def build_attendance_by_village() -> list[dict[str, Any]]:
    """Attendance aggregates grouped by village."""
    return _query(
        """
        SELECT m.village,
               COUNT(*) AS records,
               SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END)
                 AS present_like,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absents
        FROM attendance a
        JOIN members m ON a.member_id = m.national_id
        GROUP BY m.village
        ORDER BY present_like DESC
        """,
        fetch="all",
    ) or []


def build_kpi_snapshot() -> dict[str, Any]:
    """
    Compact KPI snapshot combining completion rate and low-stock pressure.
    """
    community = build_community_metrics()
    inventory = build_inventory_summary()
    return {
        "completion_rate": community["completion_rate"],
        "ongoing_projects": community["ongoing_projects"],
        "low_stock_items": len(inventory["low_stock"]),
        "open_borrows": len(inventory["borrowed"]),
        "active_members": community["active_members"],
    }


# =============================================================================
# Console presentation
# =============================================================================
def community_summary() -> None:
    """Print high-level community totals."""
    helpers.print_line(
        languages.t("community_summary_title", fallback="COMMUNITY SUMMARY")
    )
    try:
        m = build_community_metrics()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    print("Total members:", m["total_members"])
    print("Active members:", m["active_members"])
    print("Total projects:", m["total_projects"])
    print("Ongoing projects:", m["ongoing_projects"])
    print("Completed projects:", m["completed_projects"])
    print(
        languages.t("project_completion_rate", fallback="Completion rate:"),
        f"{m['completion_rate']}%",
    )
    print("Tool types:", m["tool_types"])
    print("Available tool units:", m["available_tool_units"])
    print("Umuganda dates recorded:", m["attendance_days"])
    helpers.pause()


def member_report() -> None:
    """Print member counts by status and village."""
    helpers.print_line(languages.t("member_report_title", fallback="MEMBER REPORT"))
    try:
        data = build_member_breakdown()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    print("\n--- By status ---")
    if not data["by_status"]:
        print("No members.")
    else:
        for row in data["by_status"]:
            print(f"{row['status']}: {row['total']}")

    print("\n--- By village ---")
    if not data["by_village"]:
        print("No village data.")
    else:
        for row in data["by_village"]:
            print(f"{row['village']}: {row['total']}")
    helpers.pause()


def attendance_summary() -> None:
    """Print attendance status breakdown and present/late rate."""
    helpers.print_line(
        languages.t("attendance_summary_title", fallback="ATTENDANCE SUMMARY")
    )
    try:
        data = build_attendance_summary()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    if not data["by_status"]:
        print("No attendance data.")
    else:
        for row in data["by_status"]:
            print(f"{row['status']}: {row['total']}")

    pct = data["avg_present_pct"]
    if pct is None:
        print("Overall present/late rate: N/A (no attendance data yet)")
    else:
        print("Overall present/late rate:", pct, "%")
    helpers.pause()


def most_active_members() -> None:
    """Print top members by present/late counts."""
    helpers.print_line(
        languages.t("most_active_title", fallback="MOST ACTIVE MEMBERS")
    )
    try:
        rows = build_most_active_members()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    if not rows:
        print("No data.")
    else:
        for row in rows:
            print(
                row["first_name"],
                row["last_name"],
                f"({row['village']}) -",
                row["active_count"],
                "present/late",
            )
    helpers.pause()


def poor_attendance_members() -> None:
    """Print members with repeated absences."""
    helpers.print_line(
        languages.t("poor_attendance_title", fallback="POOR ATTENDANCE")
    )
    try:
        rows = build_poor_attendance()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    if not rows:
        print("No poor attendance found.")
    else:
        for row in rows:
            print(
                row["first_name"],
                row["last_name"],
                "| phone:",
                row["phone"],
                "| absents:",
                row["absent_count"],
            )
    helpers.pause()


def project_summary() -> None:
    """Print project status aggregates, incomplete and overdue lists."""
    helpers.print_line(
        languages.t("project_summary_title", fallback="PROJECT SUMMARY")
    )
    try:
        data = build_project_summary()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    if not data["by_status"]:
        print("No projects.")
    else:
        for row in data["by_status"]:
            print(
                f"{row['status']}: {row['total']} projects | "
                f"avg progress: {safe_num(row['avg_progress'])}%"
            )

    print("\n--- Incomplete projects ---")
    if not data["incomplete"]:
        print("None")
    else:
        for row in data["incomplete"]:
            print(
                row["project_name"],
                "|",
                row["status"],
                "|",
                f"{row['percent_complete']}% | due",
                row["expected_end_date"],
            )

    print("\n--- Overdue projects ---")
    if not data["overdue"]:
        print("None")
    else:
        for row in data["overdue"]:
            print(
                row["project_name"],
                "|",
                row["status"],
                "|",
                f"{row['percent_complete']}% | due",
                row["expected_end_date"],
            )
    helpers.pause()


def inventory_summary() -> None:
    """Print tool inventory, low stock, and open borrows."""
    helpers.print_line(
        languages.t("inventory_summary_title", fallback="INVENTORY SUMMARY")
    )
    try:
        data = build_inventory_summary()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    totals = data["totals"]
    print("Tool types:", safe_num(totals.get("tool_types")))
    print("Total units:", safe_num(totals.get("total_units")))
    print("Available units:", safe_num(totals.get("available_units")))

    print("\n--- By condition ---")
    if not data["by_condition"]:
        print("No tools.")
    else:
        for row in data["by_condition"]:
            print(f"{row['condition_status']}: {row['total']}")

    print("\n--- Low stock ---")
    if not data["low_stock"]:
        print("None")
    else:
        for row in data["low_stock"]:
            print(
                row["tool_name"],
                ":",
                row["available_quantity"],
                "left (limit",
                row["low_stock_limit"],
                ")",
            )

    print("\n--- Currently borrowed ---")
    if not data["borrowed"]:
        print("No open borrows.")
    else:
        for row in data["borrowed"]:
            print(
                row["tool_name"],
                "x",
                row["quantity"],
                "->",
                row["first_name"],
                row["last_name"],
                "since",
                row["borrow_date"],
            )
    helpers.pause()


def attendance_by_village() -> None:
    """Print attendance aggregates per village."""
    helpers.print_line(
        languages.t("attendance_by_village_title", fallback="ATTENDANCE BY VILLAGE")
    )
    try:
        rows = build_attendance_by_village()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    if not rows:
        print("No data.")
    else:
        for row in rows:
            print(
                row["village"],
                "| records:",
                row["records"],
                "| present/late:",
                row["present_like"],
                "| absent:",
                row["absents"],
            )
    helpers.pause()


def kpi_snapshot_report() -> None:
    """Print compact operational KPIs for quick leader review."""
    helpers.print_line(languages.t("kpi_snapshot_title", fallback="KPI SNAPSHOT"))
    try:
        kpi = build_kpi_snapshot()
    except ReportQueryError as exc:
        helpers.error(str(exc))
        helpers.pause()
        return

    print("Active members:", kpi["active_members"])
    print("Ongoing projects:", kpi["ongoing_projects"])
    print("Project completion rate:", f"{kpi['completion_rate']}%")
    print("Low-stock tool types:", kpi["low_stock_items"])
    print("Open tool borrows:", kpi["open_borrows"])
    helpers.pause()


# =============================================================================
# File exports
# =============================================================================
def export_community_summary() -> None:
    """Export community KPIs to a timestamped text file under exports/."""
    helpers.print_line(
        languages.t("export_community_title", fallback="EXPORT COMMUNITY SUMMARY")
    )
    try:
        m = build_community_metrics()
        filepath = _export_filename("community_summary")
        lines = [
            "COMMUNITY SUMMARY",
            "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
            f"Total members: {m['total_members']}",
            f"Active members: {m['active_members']}",
            f"Total projects: {m['total_projects']}",
            f"Ongoing projects: {m['ongoing_projects']}",
            f"Completed projects: {m['completed_projects']}",
            f"Completion rate: {m['completion_rate']}%",
            f"Tool types: {m['tool_types']}",
            f"Available tool units: {m['available_tool_units']}",
            f"Umuganda dates recorded: {m['attendance_days']}",
        ]
        path = _write_export(filepath, lines)
        helpers.success(f"Exported to {path}")
    except (ReportQueryError, ReportExportError) as exc:
        helpers.error(str(exc))
    helpers.pause()


def export_project_summary() -> None:
    """Export project status and incomplete/overdue lists to exports/."""
    helpers.print_line(
        languages.t("export_project_title", fallback="EXPORT PROJECT SUMMARY")
    )
    try:
        data = build_project_summary()
        filepath = _export_filename("project_summary")
        lines = [
            "PROJECT SUMMARY",
            "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
        ]
        if not data["by_status"]:
            lines.append("No projects.")
        else:
            for row in data["by_status"]:
                lines.append(
                    f"{row['status']}: {row['total']} projects | "
                    f"avg progress: {safe_num(row['avg_progress'])}%"
                )
        lines.append("")
        lines.append("--- Incomplete projects ---")
        if not data["incomplete"]:
            lines.append("None")
        else:
            for row in data["incomplete"]:
                lines.append(
                    f"{row['project_name']} | {row['status']} | "
                    f"{row['percent_complete']}% | due {row['expected_end_date']}"
                )
        lines.append("")
        lines.append("--- Overdue projects ---")
        if not data["overdue"]:
            lines.append("None")
        else:
            for row in data["overdue"]:
                lines.append(
                    f"{row['project_name']} | {row['status']} | "
                    f"{row['percent_complete']}% | due {row['expected_end_date']}"
                )
        path = _write_export(filepath, lines)
        helpers.success(f"Exported to {path}")
    except (ReportQueryError, ReportExportError) as exc:
        helpers.error(str(exc))
    helpers.pause()


def export_attendance_summary() -> None:
    """Export attendance status breakdown to exports/."""
    helpers.print_line(
        languages.t("export_attendance_title", fallback="EXPORT ATTENDANCE SUMMARY")
    )
    try:
        data = build_attendance_summary()
        filepath = _export_filename("attendance_summary")
        lines = [
            "ATTENDANCE SUMMARY",
            "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
        ]
        if not data["by_status"]:
            lines.append("No attendance data.")
        else:
            for row in data["by_status"]:
                lines.append(f"{row['status']}: {row['total']}")
        pct = data["avg_present_pct"]
        lines.append("")
        lines.append(
            "Overall present/late rate: "
            + ("N/A" if pct is None else f"{pct}%")
        )
        path = _write_export(filepath, lines)
        helpers.success(f"Exported to {path}")
    except (ReportQueryError, ReportExportError) as exc:
        helpers.error(str(exc))
    helpers.pause()


def export_community_summary_csv() -> None:
    """
    Export community KPIs as CSV (Metric, Value) under exports/.

    Uses the same metric builder as the text/community console reports
    so on-screen and exported numbers stay consistent.
    """
    helpers.print_line(
        languages.t(
            "export_community_csv_title",
            fallback="EXPORT COMMUNITY SUMMARY (CSV)",
        )
    )
    try:
        m = build_community_metrics()
        filepath = make_export_filename("community_summary", "csv")
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Total members", m["total_members"]])
                writer.writerow(["Active members", m["active_members"]])
                writer.writerow(["Total projects", m["total_projects"]])
                writer.writerow(["Ongoing projects", m["ongoing_projects"]])
                writer.writerow(["Completed projects", m["completed_projects"]])
                writer.writerow(["Completion rate (%)", m["completion_rate"]])
                writer.writerow(["Tool types", m["tool_types"]])
                writer.writerow(["Available tool units", m["available_tool_units"]])
                writer.writerow(["Umuganda dates recorded", m["attendance_days"]])
        except OSError as exc:
            raise ReportExportError(f"Could not write {filepath}: {exc}") from exc
        helpers.success(f"Exported to {filepath}")
    except (ReportQueryError, ReportExportError) as exc:
        helpers.error(str(exc))
    helpers.pause()


# =============================================================================
# Menu
# =============================================================================
def reports_menu() -> None:
    """
    Interactive reports menu for village leaders.

    Options cover community, members, attendance, projects, inventory,
    KPI snapshot, and file exports (TXT + CSV).
    """
    running = True
    while running:
        helpers.print_line(languages.t("reports_menu"))
        print(languages.t("r1", fallback="1. Community summary"))
        print(languages.t("r2", fallback="2. Member report"))
        print(languages.t("r3", fallback="3. Attendance summary"))
        print(languages.t("r4", fallback="4. Most active members"))
        print(languages.t("r5", fallback="5. Poor attendance"))
        print(languages.t("r6", fallback="6. Project summary"))
        print(languages.t("r7", fallback="7. Inventory summary"))
        print(languages.t("r8", fallback="8. Attendance by village"))
        print(
            languages.t(
                "r9",
                fallback="9. Export community summary to file",
            )
        )
        print(
            languages.t(
                "r10",
                fallback="10. Export project summary to file",
            )
        )
        print("11. " + languages.t("kpi_snapshot_title", fallback="KPI snapshot"))
        print(
            "12. "
            + languages.t(
                "export_attendance_title",
                fallback="Export attendance summary to file",
            )
        )
        print(
            "13. "
            + languages.t(
                "export_community_csv_title",
                fallback="Export community summary to CSV",
            )
        )
        print(languages.t("r0", fallback="0. Back"))
        try:
            choice = helpers.input_with_exit(languages.t("enter_choice"))
        except ExitRequested:
            print(
                languages.t(
                    "returning_main_menu",
                    fallback="Returning to main menu...",
                )
            )
            running = False
            continue

        if choice == "1":
            community_summary()
        elif choice == "2":
            member_report()
        elif choice == "3":
            attendance_summary()
        elif choice == "4":
            most_active_members()
        elif choice == "5":
            poor_attendance_members()
        elif choice == "6":
            project_summary()
        elif choice == "7":
            inventory_summary()
        elif choice == "8":
            attendance_by_village()
        elif choice == "9":
            export_community_summary()
        elif choice == "10":
            export_project_summary()
        elif choice == "11":
            kpi_snapshot_report()
        elif choice == "12":
            export_attendance_summary()
        elif choice == "13":
            export_community_summary_csv()
        elif choice == "0":
            print(
                languages.t(
                    "returning_main_menu",
                    fallback="Returning to main menu...",
                )
            )
            running = False
        else:
            helpers.error(languages.t("invalid_choice", fallback="Invalid choice."))


__all__ = [
    "reports_menu",
    "community_summary",
    "member_report",
    "attendance_summary",
    "most_active_members",
    "poor_attendance_members",
    "project_summary",
    "inventory_summary",
    "attendance_by_village",
    "kpi_snapshot_report",
    "export_community_summary",
    "export_project_summary",
    "export_attendance_summary",
    "export_community_summary_csv",
    "make_export_filename",
    "build_community_metrics",
    "build_kpi_snapshot",
    "safe_num",
    "safe_row",
    "ReportError",
    "ReportQueryError",
    "ReportExportError",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reports_menu()
