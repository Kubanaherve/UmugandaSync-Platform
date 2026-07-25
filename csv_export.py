# csv_export.py
# Production-ready CSV export for UmugandaSync
# Supports members, attendance, projects, and tools export

import csv
import os
from datetime import datetime
import database
import helpers
import languages
import config


EXPORT_DIR = getattr(config, "CSV_EXPORT_DIR", "exports")


def ensure_export_dir():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR, exist_ok=True)


def _get_export_path(filename):
    ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename, ext = os.path.splitext(filename)
    return os.path.join(EXPORT_DIR, f"{basename}_{timestamp}{ext}")


def _write_csv(filepath, headers, rows):
    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return True
    except (IOError, OSError, csv.Error) as e:
        helpers.error(languages.t("csv_write_error") + " " + str(e))
        return False


def _report_success(filepath, count):
    abs_path = os.path.abspath(filepath)
    helpers.success(
        languages.t("csv_exported").format(count=count, path=abs_path)
    )
    helpers.tip(languages.t("csv_export_tip"))


def export_members():
    helpers.print_line(languages.t("csv_export_members"))
    rows = database.run_query(
        """SELECT member_id, national_id, first_name, last_name, phone,
                  village, cell_name, gender, date_registered, status
           FROM members ORDER BY member_id""",
        fetch="all"
    )
    if not rows:
        helpers.warning(languages.t("csv_no_data"))
        helpers.pause()
        return

    headers = [
        "Member ID", "National ID", "First Name", "Last Name", "Phone",
        "Village", "Cell", "Gender", "Date Registered", "Status"
    ]
    data = [[
        r["member_id"], r["national_id"] or "", r["first_name"], r["last_name"],
        r["phone"], r["village"], r["cell_name"], r["gender"],
        str(r["date_registered"]), r["status"]
    ] for r in rows]

    filepath = _get_export_path("members.csv")
    if _write_csv(filepath, headers, data):
        _report_success(filepath, len(rows))
    helpers.pause()


def export_attendance():
    helpers.print_line(languages.t("csv_export_attendance"))

    date_filter = None
    print()
    filter_choice = input(languages.t("csv_date_filter_prompt")).strip().lower()
    if filter_choice in ("y", "yes", "o", "oui"):
        date_filter = helpers.get_date(languages.t("csv_date_prompt"))

    if date_filter:
        rows = database.run_query(
            """SELECT a.attendance_id, a.member_id, m.first_name, m.last_name,
                      m.village, a.attendance_date, a.status, a.remarks
               FROM attendance a
               JOIN members m ON a.member_id = m.member_id
               WHERE a.attendance_date = %s
               ORDER BY m.village, m.last_name""",
            (date_filter,),
            fetch="all"
        )
    else:
        rows = database.run_query(
            """SELECT a.attendance_id, a.member_id, m.first_name, m.last_name,
                      m.village, a.attendance_date, a.status, a.remarks
               FROM attendance a
               JOIN members m ON a.member_id = m.member_id
               ORDER BY a.attendance_date DESC, m.village, m.last_name""",
            fetch="all"
        )

    if not rows:
        helpers.warning(languages.t("csv_no_data"))
        helpers.pause()
        return

    headers = [
        "Attendance ID", "Member ID", "First Name", "Last Name",
        "Village", "Date", "Status", "Remarks"
    ]
    data = [[
        r["attendance_id"], r["member_id"], r["first_name"], r["last_name"],
        r["village"], str(r["attendance_date"]), r["status"], r["remarks"] or ""
    ] for r in rows]

    filepath = _get_export_path("attendance.csv")
    if _write_csv(filepath, headers, data):
        _report_success(filepath, len(rows))
    helpers.pause()


def export_projects():
    helpers.print_line(languages.t("csv_export_projects"))
    rows = database.run_query(
        """SELECT p.project_id, p.project_name, p.description, p.location,
                  p.leader_member_id, m.first_name, m.last_name,
                  p.start_date, p.expected_end_date, p.status, p.percent_complete
           FROM projects p
           LEFT JOIN members m ON p.leader_member_id = m.member_id
           ORDER BY p.start_date DESC""",
        fetch="all"
    )
    if not rows:
        helpers.warning(languages.t("csv_no_data"))
        helpers.pause()
        return

    headers = [
        "Project ID", "Project Name", "Description", "Location",
        "Leader ID", "Leader Name", "Start Date", "Expected End Date",
        "Status", "Percent Complete"
    ]
    data = [[
        r["project_id"], r["project_name"], r["description"] or "",
        r["location"], r["leader_member_id"] or "",
        (r["first_name"] or "") + " " + (r["last_name"] or ""),
        str(r["start_date"]), str(r["expected_end_date"]),
        r["status"], str(r["percent_complete"])
    ] for r in rows]

    filepath = _get_export_path("projects.csv")
    if _write_csv(filepath, headers, data):
        _report_success(filepath, len(rows))
    helpers.pause()


def export_tools():
    helpers.print_line(languages.t("csv_export_tools"))
    rows = database.run_query(
        """SELECT tool_id, tool_name, category, total_quantity,
                  available_quantity, condition_status, low_stock_limit
           FROM tools ORDER BY tool_name""",
        fetch="all"
    )
    if not rows:
        helpers.warning(languages.t("csv_no_data"))
        helpers.pause()
        return

    headers = [
        "Tool ID", "Tool Name", "Category", "Total Quantity",
        "Available Quantity", "Condition", "Low Stock Limit"
    ]
    low_stock_count = 0
    data = []
    for r in rows:
        is_low = r["available_quantity"] <= r["low_stock_limit"]
        if is_low:
            low_stock_count += 1
        data.append([
            r["tool_id"], r["tool_name"], r["category"],
            r["total_quantity"], r["available_quantity"],
            r["condition_status"], r["low_stock_limit"]
        ])

    filepath = _get_export_path("tools.csv")
    if _write_csv(filepath, headers, data):
        _report_success(filepath, len(rows))
        if low_stock_count > 0:
            helpers.warning(
                languages.t("csv_low_stock_note").format(n=low_stock_count)
            )
    helpers.pause()


def export_community_summary():
    helpers.print_line(languages.t("csv_export_summary"))
    ensure_export_dir()

    total_m = database.run_query("SELECT COUNT(*) AS t FROM members", fetch="one")
    active_m = database.run_query(
        "SELECT COUNT(*) AS t FROM members WHERE status='Active'", fetch="one"
    )
    total_p = database.run_query("SELECT COUNT(*) AS t FROM projects", fetch="one")
    ongoing_p = database.run_query(
        "SELECT COUNT(*) AS t FROM projects WHERE status='Ongoing'", fetch="one"
    )
    total_a = database.run_query(
        "SELECT COUNT(DISTINCT attendance_date) AS t FROM attendance", fetch="one"
    )
    total_t = database.run_query("SELECT COUNT(*) AS t FROM tools", fetch="one")

    rows = [
        ["Metric", "Value"],
        ["Total Members", str(total_m["t"] if total_m else 0)],
        ["Active Members", str(active_m["t"] if active_m else 0)],
        ["Total Projects", str(total_p["t"] if total_p else 0)],
        ["Ongoing Projects", str(ongoing_p["t"] if ongoing_p else 0)],
        ["Umuganda Dates", str(total_a["t"] if total_a else 0)],
        ["Tool Types", str(total_t["t"] if total_t else 0)],
    ]
    headers = ["Metric", "Value"]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows.append(["Export Date", timestamp])

    filepath = _get_export_path("community_summary.csv")
    if _write_csv(filepath, headers, rows[1:]):
        _report_success(filepath, len(rows) - 1)
    helpers.pause()


def show_csv_export_menu():
    running = True
    while running:
        helpers.print_line(languages.t("csv_export_menu"))
        print(languages.t("csv_e1"))
        print(languages.t("csv_e2"))
        print(languages.t("csv_e3"))
        print(languages.t("csv_e4"))
        print(languages.t("csv_e5"))
        print(languages.t("csv_e0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            export_members()
        elif choice == "2":
            export_attendance()
        elif choice == "3":
            export_projects()
        elif choice == "4":
            export_tools()
        elif choice == "5":
            export_community_summary()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))
