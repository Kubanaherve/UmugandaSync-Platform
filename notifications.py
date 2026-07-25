"""
Notification center for UmugandaSync.

Scans for low-stock tools, overdue projects, broken equipment,
absent members, and new registrations, then displays structured
warnings and informational messages.
"""

import logging
from datetime import datetime
from typing import Any, Callable

import database
import helpers
import tools
import projects
import languages

logger = logging.getLogger(__name__)

_warnings_count: int = 0
_info_count: int = 0

_notification_checks: list[Callable[[], None]] = []


def _safe_get(sql: str, params: tuple = ()) -> Any:
    try:
        return database.run_query(sql, params, fetch="one")
    except Exception as e:
        logger.error(f"Notification query failed: {e}")
        return None


def _safe_get_all(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        return database.run_query(sql, params, fetch="all") or []
    except Exception as e:
        logger.error(f"Notification query failed: {e}")
        return []


def register_notification_check(check_func: Callable[[], None]) -> None:
    _notification_checks.append(check_func)
    logger.debug(f"Registered notification check: {check_func.__name__}")


def show_notifications() -> None:
    global _warnings_count, _info_count
    _warnings_count = 0
    _info_count = 0
    helpers.print_line(languages.t("notifications"))
    found = False

    low_count = tools.count_low_stock_tools()
    if low_count > 0:
        found = True
        msg = languages.t("warn_low_stock").replace("{n}", str(low_count))
        _show_warning(msg)

    overdue_names = projects.list_overdue_project_names()
    if overdue_names:
        _show_separator()
        for name in overdue_names:
            found = True
            msg = languages.t("warn_overdue").replace("{name}", name)
            _show_warning(msg)

    broken_tools = _safe_get_all(
        "SELECT tool_name, total_quantity FROM tools WHERE condition_status='Broken'"
    )
    if broken_tools:
        _show_separator()
        for tool in broken_tools:
            found = True
            _show_warning(
                languages.t("tool_broken_warning").format(
                    name=tool["tool_name"], qty=tool["total_quantity"]
                )
            )

    now = datetime.now()
    umuganda = helpers.get_last_saturday(now.year, now.month)
    umuganda_text = umuganda.strftime("%Y-%m-%d")
    month_name = helpers.MONTH_NAMES[now.month]

    umuganda_row = _safe_get(
        "SELECT COUNT(*) AS total FROM attendance WHERE attendance_date = %s",
        (umuganda_text,),
    )
    if umuganda_row is not None:
        if umuganda_row["total"] == 0:
            found = True
            _show_info(
                languages.t("notice_no_attendance_month").format(
                    date=umuganda_text, month=month_name
                )
            )
        else:
            absent_row = _safe_get(
                """SELECT COUNT(*) AS total FROM attendance
                   WHERE attendance_date = %s AND status = 'Absent'""",
                (umuganda_text,),
            )
            if absent_row is not None and absent_row["total"] > 0:
                found = True
                _show_warning(
                    languages.t("notice_absents").format(
                        n=absent_row["total"], date=umuganda_text
                    )
                )
            present_count = umuganda_row["total"] - (
                absent_row["total"] if absent_row else 0
            )
            _show_info(
                languages.t("attendance_summary_notice").format(
                    total=umuganda_row["total"],
                    present=present_count,
                    date=umuganda_text,
                )
            )

    latest = _safe_get(
        "SELECT MAX(attendance_date) AS latest_date FROM attendance"
    )
    if latest is not None and latest["latest_date"] is not None:
        _show_info(languages.t("latest_umuganda").format(date=latest["latest_date"]))

    total_active = _safe_get(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'"
    )
    if total_active is not None:
        _show_info(languages.t("active_member_count").format(n=total_active["total"]))

    new_members = _safe_get(
        "SELECT COUNT(*) AS total FROM members WHERE date_registered >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    )
    if new_members and new_members["total"] > 0:
        found = True
        _show_separator()
        _show_info(
            languages.t("welcome_new_members").format(n=new_members["total"])
        )

    for check in _notification_checks:
        check()

    if not found:
        print("  " + languages.t("no_warnings"))
    else:
        _show_separator()
        print(
            "  "
            + languages.t("notification_summary").format(
                w=_warnings_count, i=_info_count
            )
        )
    print()


def _show_separator() -> None:
    print("  " + "-" * 40)


def _show_success(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    helpers.success(f"  \u2713 SUCCESS [{timestamp}]: {message}")


def _show_error(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    helpers.error(f"  \u2717 ERROR [{timestamp}]: {message}")


def _show_warning(message: str) -> None:
    global _warnings_count
    _warnings_count += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  \u26A0 WARNING [{timestamp}]: {message}")


def _show_info(message: str) -> None:
    global _info_count
    _info_count += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  \u2139 INFO [{timestamp}]: {message}")
