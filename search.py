"""
Universal search module for UmugandaSync.

Provides search across members, projects, tools, and attendance
with a pluggable handler registry. Also exports validate_national_id
from helpers for backward compatibility with tests.
"""

import logging
from typing import Any, Callable, Optional

import database
import helpers
import languages

logger = logging.getLogger(__name__)

SEARCH_HANDLERS: dict[str, Callable[..., None]] = {}

validate_national_id = helpers.validate_national_id
validate_email = helpers.validate_email


def _safe_db_query(sql: str, params: tuple = (), fetch: str = "all") -> Any:
    try:
        result = database.run_query(sql, params, fetch=fetch)
        if result is None:
            return [] if fetch == "all" else None
        return result
    except Exception as e:
        logger.error(f"Search query failed: {e}")
        return [] if fetch == "all" else None


def register_search_handler(name: str, handler_func: Callable[..., None]) -> None:
    SEARCH_HANDLERS[name] = handler_func
    logger.debug(f"Search handler registered: '{name}'")


def get_search_handler(name: str) -> Optional[Callable[..., None]]:
    return SEARCH_HANDLERS.get(name)


def search_menu() -> None:
    running = True
    while running:
        helpers.print_line(languages.t("search_menu"))
        print(languages.t("s1"))
        print(languages.t("s2"))
        print(languages.t("s3"))
        print(languages.t("s4"))
        print(languages.t("s5"))
        print(languages.t("search_by_email"))
        print(languages.t("s0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            search_members()
        elif choice == "2":
            search_projects()
        elif choice == "3":
            search_tools()
        elif choice == "4":
            search_attendance_date()
        elif choice == "5":
            search_by_national_id()
        elif choice == "6":
            search_by_email()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


def search_members() -> None:
    text = helpers.get_non_empty(languages.t("search_term_prompt"))
    like_text = "%" + text + "%"

    if text.isdigit():
        rows = _safe_db_query(
            """SELECT * FROM members
               WHERE member_id = %s OR phone LIKE %s
                  OR first_name LIKE %s OR last_name LIKE %s""",
            (int(text), like_text, like_text, like_text),
            fetch="all",
        )
    else:
        rows = _safe_db_query(
            """SELECT * FROM members
               WHERE phone LIKE %s OR first_name LIKE %s OR last_name LIKE %s""",
            (like_text, like_text, like_text),
            fetch="all",
        )

    _display_member_results(rows)


def search_by_national_id() -> None:
    helpers.print_line(languages.t("s5_title"))
    print(languages.t("s5_help"))
    print()

    while True:
        national_id = helpers.get_non_empty(languages.t("s5_prompt"))
        if national_id == "0":
            return

        is_valid, msg_or_nid = helpers.validate_rwanda_national_id(national_id)
        if not is_valid:
            helpers.error(msg_or_nid)
            print()
            continue

        helpers.info(languages.t("searching_id") + " " + msg_or_nid)
        print()

        row = search_member_by_national_id(msg_or_nid)

        if not row:
            helpers.warning(languages.t("s5_not_found"))
            print()
            helpers.tip(languages.t("s5_not_found_tip"))
            print()
            choice = input(languages.t("search_again")).strip().lower()
            if choice != "y":
                break
        else:
            helpers.success(languages.t("s5_found"))
            print()
            _display_detailed_member(row)
            break

    helpers.pause()


def search_member_by_national_id(national_id: str) -> Optional[dict[str, Any]]:
    is_valid, result = helpers.validate_rwanda_national_id(national_id)
    if not is_valid:
        return None
    row = _safe_db_query(
        """SELECT member_id, national_id, first_name, last_name, phone,
                  village, cell_name, gender, status, date_registered
           FROM members WHERE national_id = %s""",
        (result,),
        fetch="one",
    )
    return row


def search_by_email() -> None:
    helpers.print_line(languages.t("s6_title"))
    print(languages.t("s6_help"))
    print()

    while True:
        email_input = helpers.get_non_empty(languages.t("s6_prompt"))
        if email_input == "0":
            break

        is_valid, clean_email = validate_email(email_input)
        if not is_valid:
            helpers.error(clean_email)
            print()
            continue

        row = _safe_db_query(
            """SELECT member_id, national_id, first_name, last_name, phone,
                      village, cell_name, gender, status, date_registered
               FROM members WHERE email = %s""",
            (clean_email,),
            fetch="one",
        )

        if not row:
            helpers.warning(languages.t("s6_not_found"))
            print()
            helpers.tip(languages.t("s6_not_found_tip"))
            print()
            choice = input(languages.t("search_again")).strip().lower()
            if choice != "y":
                break
        else:
            helpers.success(languages.t("s6_found"))
            print()
            _display_detailed_member(row)
            break

    helpers.pause()


def _display_detailed_member(row: dict[str, Any]) -> None:
    helpers.print_line(languages.t("member_details"))
    print(f"{languages.t('first_name')}: {row['first_name']}")
    print(f"{languages.t('last_name')}: {row['last_name']}")
    print(f"{languages.t('national_id')}: {row['national_id']}")
    print(f"{languages.t('phone')}: {row['phone']}")
    email_val = row.get("email", "")
    if email_val:
        print(f"{languages.t('email')}: {email_val}")
    print(f"{languages.t('gender')}: {row.get('gender', 'N/A')}")
    print(f"{languages.t('village')}: {row['village']}")
    print(f"{languages.t('cell_name')}: {row.get('cell_name', 'N/A')}")
    print(f"{languages.t('status')}: {row['status']}")
    print(f"{languages.t('date_registered')}: {row.get('date_registered', 'N/A')}")

    stats = _safe_db_query(
        """SELECT COUNT(*) as total_events,
                  SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count
           FROM attendance WHERE member_id = %s""",
        (row["member_id"],),
        fetch="one",
    )

    print()
    helpers.print_line(languages.t("attendance_stats"))
    if stats and stats["total_events"] > 0:
        total = stats["total_events"]
        present = int(stats["present_count"] or 0)
        percentage = (present / total) * 100
        print(f"{languages.t('total_events')}: {total}")
        print(f"{languages.t('present')}: {present} ({percentage:.1f}%)")
    else:
        print(languages.t("no_attendance_records"))
    print()


def _display_member_results(rows: Any) -> None:
    if not rows:
        print(languages.t("no_results"))
    else:
        for row in rows:
            nid = row["national_id"] if row["national_id"] else "N/A"
            print(
                "ID:", str(row["member_id"]).rjust(4),
                "|", row["first_name"].ljust(15), row["last_name"].ljust(15),
                "|", row["phone"].ljust(12),
                "|", row["village"].ljust(12),
                "|", row["status"].ljust(10),
                "| NID:", nid,
            )
        print()
        helpers.success(languages.t("total") + ": " + str(len(rows)))
    helpers.pause()


def search_projects() -> None:
    name = helpers.get_non_empty(languages.t("project_name_contains"))
    like_name = "%" + name + "%"
    rows = _safe_db_query(
        """SELECT project_id, project_name, status, percent_complete, location
           FROM projects WHERE project_name LIKE %s""",
        (like_name,),
        fetch="all",
    )
    if not rows:
        print(languages.t("no_results"))
    else:
        for row in rows:
            print(
                str(row["project_id"]).rjust(4),
                "|", row["project_name"].ljust(30),
                "|", row["status"].ljust(12),
                "|", str(row["percent_complete"]) + "%",
                "|", row["location"],
            )
        print()
        print(languages.t("total") + ":", len(rows))
    helpers.pause()


def search_tools() -> None:
    name = helpers.get_non_empty(languages.t("tool_name_contains"))
    like_name = "%" + name + "%"
    rows = _safe_db_query(
        """SELECT tool_id, tool_name, available_quantity, total_quantity, condition_status
           FROM tools WHERE tool_name LIKE %s""",
        (like_name,),
        fetch="all",
    )
    if not rows:
        print(languages.t("no_results"))
    else:
        for row in rows:
            print(
                str(row["tool_id"]).rjust(4),
                "|", row["tool_name"].ljust(20),
                "|", str(row["available_quantity"]).rjust(3),
                "/", str(row["total_quantity"]).rjust(3),
                "|", row["condition_status"],
            )
        print()
        print(languages.t("total") + ":", len(rows))
    helpers.pause()


def search_attendance_date() -> None:
    helpers.tip(languages.t("choose_month_tip"))
    month_info = helpers.ask_umuganda_month()
    if month_info is None:
        helpers.pause()
        return
    the_date = month_info[0]
    rows = _safe_db_query(
        """SELECT a.attendance_date, a.status, a.remarks, m.first_name, m.last_name
           FROM attendance a
           JOIN members m ON a.member_id = m.member_id
           WHERE a.attendance_date = %s
           ORDER BY m.first_name""",
        (the_date,),
        fetch="all",
    )
    if not rows:
        print(languages.t("no_results"))
    else:
        for row in rows:
            print(
                row["attendance_date"],
                "|", row["first_name"].ljust(15), row["last_name"].ljust(15),
                "|", row["status"].ljust(10),
                "|", row["remarks"],
            )
        print()
        print(languages.t("total") + ":", len(rows))
    helpers.pause()


def quick_search(search_term: str) -> dict[str, list[dict[str, Any]]]:
    if not search_term:
        return {"members": [], "projects": [], "tools": []}

    like_text = f"%{search_term}%"

    members = _safe_db_query(
        """SELECT member_id, first_name, last_name, phone, status
           FROM members
           WHERE first_name LIKE %s OR last_name LIKE %s OR phone LIKE %s""",
        (like_text, like_text, like_text),
        fetch="all",
    )

    projects = _safe_db_query(
        """SELECT project_id, project_name, status, percent_complete
           FROM projects
           WHERE project_name LIKE %s OR location LIKE %s""",
        (like_text, like_text),
        fetch="all",
    )

    tools = _safe_db_query(
        """SELECT tool_id, tool_name, available_quantity, condition_status
           FROM tools
           WHERE tool_name LIKE %s""",
        (like_text,),
        fetch="all",
    )

    return {
        "members": members or [],
        "projects": projects or [],
        "tools": tools or [],
    }


register_search_handler("members", search_members)
register_search_handler("projects", search_projects)
register_search_handler("tools", search_tools)
register_search_handler("attendance", search_attendance_date)
register_search_handler("national_id", search_by_national_id)
