"""
csv_export.py
Owner: Sonia
CSV export module for UmugandaSync.

Provides interactive menu and helpers to export database tables
(members, attendance, projects, tools) to CSV files in the exports/ directory.

Public entrypoint used by main.py: ``show_csv_export_menu()``.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Optional

import database
import helpers
import languages
import config
from helpers import ExitRequested

logger = logging.getLogger(__name__)

EXPORT_DIR = config.CSV_EXPORT_DIR


def _ensure_export_dir() -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return EXPORT_DIR


def _export_filename(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(_ensure_export_dir(), f"{prefix}_{stamp}.csv")


def _write_csv(filepath: str, columns: list[str], rows: list[dict]) -> int:
    with open(filepath, "w", newline="", encoding=config.CSV_ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=config.CSV_DELIMITER)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in columns})
    return len(rows)


def export_members() -> None:
    helpers.print_line(languages.t("csv_export_members"))
    rows = database.run_query("SELECT * FROM members ORDER BY national_id", fetch="all")
    if not rows:
        print(languages.t("csv_no_data"))
    else:
        columns = [c for c in rows[0].keys()]
        path = _export_filename("members")
        count = _write_csv(path, columns, rows)
        helpers.success(languages.t("csv_exported").format(count=count, path=path))
        helpers.tip(languages.t("csv_export_tip"))
        logger.info("Exported %d members to CSV: %s", count, path)
    helpers.pause()


def export_attendance() -> None:
    helpers.print_line(languages.t("csv_export_attendance"))
    rows = database.run_query(
        """
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
               a.member_id, m.first_name, m.last_name
        FROM attendance a
        JOIN members m ON a.member_id = m.national_id
        ORDER BY a.attendance_date DESC
        """,
        fetch="all",
    )
    if not rows:
        print(languages.t("csv_no_data"))
    else:
        columns = [c for c in rows[0].keys()]
        path = _export_filename("attendance")
        count = _write_csv(path, columns, rows)
        helpers.success(languages.t("csv_exported").format(count=count, path=path))
        helpers.tip(languages.t("csv_export_tip"))
        logger.info("Exported %d attendance records to CSV: %s", count, path)
    helpers.pause()


def export_projects() -> None:
    helpers.print_line(languages.t("csv_export_projects"))
    rows = database.run_query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.national_id
        ORDER BY p.project_id
        """,
        fetch="all",
    )
    if not rows:
        print(languages.t("csv_no_data"))
    else:
        columns = [c for c in rows[0].keys()]
        path = _export_filename("projects")
        count = _write_csv(path, columns, rows)
        helpers.success(languages.t("csv_exported").format(count=count, path=path))
        helpers.tip(languages.t("csv_export_tip"))
        logger.info("Exported %d projects to CSV: %s", count, path)
    helpers.pause()


def export_tools() -> None:
    helpers.print_line(languages.t("csv_export_tools"))
    rows = database.run_query(
        """
        SELECT t.*,
              (SELECT COUNT(*) FROM tool_borrows b WHERE b.tool_id = t.tool_id AND b.status = 'Borrowed') AS currently_borrowed
        FROM tools t
        ORDER BY t.tool_id
        """,
        fetch="all",
    )
    if not rows:
        print(languages.t("csv_no_data"))
    else:
        columns = [c for c in rows[0].keys()]
        path = _export_filename("tools")
        count = _write_csv(path, columns, rows)
        helpers.success(languages.t("csv_exported").format(count=count, path=path))
        low = sum(1 for r in rows if r.get("available_quantity", 0) <= r.get("low_stock_limit", 0))
        if low > 0:
            helpers.warning(languages.t("csv_low_stock_note").format(n=low))
        helpers.tip(languages.t("csv_export_tip"))
        logger.info("Exported %d tools to CSV: %s", count, path)
    helpers.pause()


def show_csv_export_menu() -> None:
    running = True
    while running:
        helpers.print_line(languages.t("csv_export_menu"))
        print(languages.t("csv_e1"))
        print(languages.t("csv_e2"))
        print(languages.t("csv_e3"))
        print(languages.t("csv_e4"))
        print(languages.t("csv_e0"))
        try:
            choice = helpers.input_with_exit(languages.t("enter_choice"))
        except ExitRequested:
            running = False
            continue

        if choice == "1":
            export_members()
        elif choice == "2":
            export_attendance()
        elif choice == "3":
            export_projects()
        elif choice == "4":
            export_tools()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


if __name__ == "__main__":
    show_csv_export_menu()
