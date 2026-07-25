"""
Dashboard module for UmugandaSync.

Displays a comprehensive overview of community metrics including
member counts, attendance summaries, project status, tool inventory,
and upcoming Umuganda dates.
"""

import logging
from datetime import datetime
from typing import Any, Optional

import database
import helpers
import tools
import projects
import languages
import config

logger = logging.getLogger(__name__)


def _progress_bar(percent: float, width: int = 20) -> str:
    filled = int(width * percent / 100)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return "[" + bar + "] " + str(round(percent, 1)) + "%"


def _safe_count(query_result: Optional[dict]) -> int:
    if query_result is None:
        return 0
    return query_result.get("total", 0) or 0


def show_dashboard(admin_name: str) -> None:
    try:
        _render_dashboard(admin_name)
    except Exception as e:
        logger.exception(f"Dashboard rendering failed: {e}")
        helpers.error("Failed to load dashboard data. Check database connection.")
        helpers.pause()


def _render_dashboard(admin_name: str) -> None:
    helpers.clear_screen()
    helpers.print_line(
        languages.t("dashboard") + admin_name + " (v" + config.APP_VERSION + ")"
    )
    print()

    total_members = _safe_count(
        database.run_query("SELECT COUNT(*) AS total FROM members", fetch="one")
    )
    active_members = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM members WHERE status='Active'", fetch="one"
        )
    )
    inactive_members = total_members - active_members

    gender_data: list[dict[str, Any]] = (
        database.run_query(
            "SELECT gender, COUNT(*) AS count FROM members GROUP BY gender", fetch="all"
        )
        or []
    )

    today = helpers.today_string()
    today_attendance = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM attendance WHERE attendance_date = %s",
            (today,),
            fetch="one",
        )
    )

    total_attendance = _safe_count(
        database.run_query("SELECT COUNT(*) AS total FROM attendance", fetch="one")
    )
    present_late_attendance = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM attendance WHERE status IN ('Present', 'Late')",
            fetch="one",
        )
    )
    unique_dates = _safe_count(
        database.run_query(
            "SELECT COUNT(DISTINCT attendance_date) AS total FROM attendance", fetch="one"
        )
    )

    recent_activity: list[dict[str, Any]] = (
        database.run_query(
            """SELECT attendance_date, COUNT(*) AS count
               FROM attendance GROUP BY attendance_date
               ORDER BY attendance_date DESC LIMIT 3""",
            fetch="all",
        )
        or []
    )

    ongoing = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'", fetch="one"
        )
    )
    completed = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM projects WHERE status='Completed'", fetch="one"
        )
    )
    pending = _safe_count(
        database.run_query(
            "SELECT COUNT(*) AS total FROM projects WHERE status='Pending'", fetch="one"
        )
    )

    total_projects = ongoing + completed + pending
    project_completion_rate = (completed / total_projects * 100) if total_projects > 0 else 0

    available_tools = _safe_count(
        database.run_query(
            "SELECT SUM(available_quantity) AS total FROM tools", fetch="one"
        )
    )
    tool_types = _safe_count(
        database.run_query("SELECT COUNT(*) AS total FROM tools", fetch="one")
    )

    low_stock = tools.count_low_stock_tools()
    overdue = projects.count_overdue_projects()

    now = datetime.now()
    umuganda = helpers.get_last_saturday(now.year, now.month)

    attendance_rate = (
        (present_late_attendance / total_attendance * 100) if total_attendance > 0 else 0
    )

    def print_section(title: str, lines: list[str]) -> None:
        print("  \u2554" + "\u2550" * 42 + "\u2557")
        print("  \u2551  {:<40}\u2551".format(title))
        print("  \u2560" + "\u2550" * 42 + "\u2563")
        for line in lines:
            print("  \u2551  {:<40}\u2551".format(line))
        print("  \u255a" + "\u2550" * 42 + "\u255d")
        print()

    print_section(
        languages.t("section_members"),
        [
            f"{languages.t('total_members')}: {total_members}",
            f"{languages.t('active_members')}: {active_members}",
            f"{languages.t('inactive_members')}: {inactive_members}",
            "-" * 40,
            f"{languages.t('gender_distribution')}:",
        ]
        + [f"  {g['gender']}: {g['count']}" for g in gender_data],
    )

    print_section(
        languages.t("section_attendance"),
        [
            f"{languages.t('today_attendance')}: {today_attendance} ({today})",
            f"{languages.t('total_attendance_records')}: {total_attendance}",
            f"{languages.t('umuganda_dates')}: {unique_dates}",
            f"{languages.t('attendance_rate')}:",
            f"  {_progress_bar(attendance_rate)}",
            "-" * 40,
            f"{languages.t('recent_activity')}:",
        ]
        + [f"  {act['attendance_date']}: {act['count']}" for act in recent_activity],
    )

    print_section(
        languages.t("section_projects"),
        [
            f"{languages.t('ongoing_projects')}: {ongoing}",
            f"{languages.t('completed_projects')}: {completed}",
            f"{languages.t('pending_projects')}: {pending}",
            f"{languages.t('overdue_projects')}: {overdue}",
            "-" * 40,
            f"{languages.t('project_completion_rate')}:",
            f"  {_progress_bar(project_completion_rate)}",
        ],
    )

    print_section(
        languages.t("section_tools"),
        [
            f"{languages.t('tool_types')}: {tool_types}",
            f"{languages.t('available_tools')}: {available_tools}",
            f"{languages.t('low_stock_tools')}: {low_stock}",
        ],
    )

    print_section(
        languages.t("section_umuganda"),
        [
            f"{languages.t('next_umuganda')}: {umuganda.strftime('%Y-%m-%d')}",
            f"({languages.t('last_saturday_of')} {helpers.MONTH_NAMES[now.month]})",
        ],
    )

    print("  " + languages.t("section_navigation"))
    print("  " + "-" * 40)
    print("    " + languages.t("nav_hint"))
    print()

    logger.debug(f"Dashboard displayed for '{admin_name}'")
