"""Attendance management for Umuganda community sessions.

This module records individual and group attendance, produces reports,
calculates participation percentages, and summarizes member history.
"""

import database
import helpers
import members
import languages


VALID_STATUSES = ("Present", "Absent", "Excused", "Late")
ATTENDED_STATUSES = ("Present", "Late")
STATUS_CHOICES = {
    "1": "Present",
    "2": "Absent",
    "3": "Excused",
    "4": "Late",
}


def has_rows(rows):
    """Return True when a database result contains at least one row."""
    return bool(rows)


def normalize_status(status):
    """Return a supported status using consistent capitalization."""
    if not isinstance(status, str):
        return None

    cleaned_status = status.strip().title()
    if cleaned_status in VALID_STATUSES:
        return cleaned_status
    return None


def attendance_menu():
    running = True
    while running:
        helpers.print_line(languages.t("attendance_menu"))
        print(languages.t("a1"))
        print(languages.t("a2"))
        print(languages.t("a3"))
        print(languages.t("a4"))
        print(languages.t("a5"))
        print(languages.t("a6"))
        print(languages.t("a7"))
        print(languages.t("a8"))
        print(languages.t("a9"))
        print(languages.t("a0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            record_attendance()
        elif choice == "2":
            view_all_attendance()
        elif choice == "3":
            view_by_date()
        elif choice == "4":
            view_by_member()
        elif choice == "5":
            search_attendance()
        elif choice == "6":
            member_attendance_percentage()
        elif choice == "7":
            attendance_analytics()
        elif choice == "8":
            record_village_or_all_attendance()
        elif choice == "9":
            member_lifetime_summary()
        elif choice == "0":
            running = False
        else:
            print(languages.t("invalid_choice"))


def record_attendance():
    # one person for one official Umuganda (last Saturday of month)
    helpers.print_line("RECORD UMUGANDA ATTENDANCE")
    helpers.tip("You only choose the month. Date is auto-set to last Saturday.")

    member_id = helpers.get_positive_int("Member ID: ")
    if members.member_exists(member_id) == False:
        helpers.error("Member not found.")
        helpers.pause()
        return

    month_info = helpers.ask_umuganda_month()
    if month_info == None:
        helpers.pause()
        return

    attendance_date = month_info[0]
    month_name = month_info[3]
    year = month_info[1]

    existing = database.run_query(
        """
        SELECT attendance_id FROM attendance
        WHERE member_id = %s AND attendance_date = %s
        """,
        (member_id, attendance_date),
        fetch="one"
    )
    if existing != None:
        helpers.error("Attendance already recorded for this member on that Umuganda.")
        helpers.pause()
        return

    print("Status: 1=Present  2=Absent  3=Excused  4=Late")
    status_choice = input("Choose status: ").strip()
    if status_choice == "1":
        status = "Present"
    elif status_choice == "2":
        status = "Absent"
    elif status_choice == "3":
        status = "Excused"
    elif status_choice == "4":
        status = "Late"
    else:
        helpers.error("Invalid status.")
        helpers.pause()
        return

    activity = helpers.choose_umuganda_remark()
    remarks = "Umuganda " + month_name + " " + str(year) + " — " + activity

    result = database.run_query(
        """
        INSERT INTO attendance (member_id, attendance_date, status, remarks)
        VALUES (%s, %s, %s, %s)
        """,
        (member_id, attendance_date, status, remarks)
    )
    if result != None:
        helpers.success("Attendance recorded for " + attendance_date)
        print("  Remark:", remarks)
    else:
        helpers.error("Failed to record attendance.")
    helpers.pause()


def print_attendance_rows(rows):
    if rows == None or len(rows) == 0:
        print("No attendance records found.")
        return
    for row in rows:
        print(row["attendance_id"], "|", row["attendance_date"], "|",
              row["first_name"], row["last_name"],
              "(ID", str(row["member_id"]) + ")", "|",
              row["status"], "|", row["remarks"])


def view_all_attendance():
    helpers.print_line("ALL ATTENDANCE")
    rows = database.run_query(
        """
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
               a.member_id, m.first_name, m.last_name
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        ORDER BY a.attendance_date DESC, a.attendance_id DESC
        """,
        fetch="all"
    )
    print_attendance_rows(rows)
    helpers.pause()


def view_by_date():
    helpers.print_line("ATTENDANCE BY UMUGANDA MONTH")
    helpers.tip("Choose month to view that month's last-Saturday Umuganda.")
    month_info = helpers.ask_umuganda_month()
    if month_info == None:
        helpers.pause()
        return

    the_date = month_info[0]
    rows = database.run_query(
        """
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
               a.member_id, m.first_name, m.last_name
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.attendance_date = %s
        ORDER BY m.first_name
        """,
        (the_date,),
        fetch="all"
    )
    print_attendance_rows(rows)
    helpers.pause()


def view_by_member():
    helpers.print_line("ATTENDANCE BY MEMBER")
    member_id = helpers.get_positive_int("Member ID: ")
    rows = database.run_query(
        """
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
               a.member_id, m.first_name, m.last_name
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.member_id = %s
        ORDER BY a.attendance_date DESC
        """,
        (member_id,),
        fetch="all"
    )
    print_attendance_rows(rows)
    helpers.pause()


def search_attendance():
    helpers.print_line("SEARCH ATTENDANCE")
    print("1. By status (Present/Absent/Excused/Late)")
    print("2. By Umuganda month (last Saturday)")
    choice = input("Enter choice: ").strip()
    if choice == "1":
        status = helpers.get_non_empty("Status: ")
        rows = database.run_query(
            """
            SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
                   a.member_id, m.first_name, m.last_name
            FROM attendance a
            JOIN members m ON a.member_id = m.member_id
            WHERE a.status = %s
            ORDER BY a.attendance_date DESC
            """,
            (status,),
            fetch="all"
        )
        print_attendance_rows(rows)
        helpers.pause()
    elif choice == "2":
        view_by_date()
    else:
        print("Invalid choice.")
        helpers.pause()


def member_attendance_percentage():
    helpers.print_line("ATTENDANCE PERCENTAGE")
    member_id = helpers.get_positive_int("Member ID: ")
    if members.member_exists(member_id) == False:
        print("Member not found.")
        helpers.pause()
        return

    total_row = database.run_query(
        "SELECT COUNT(*) AS total FROM attendance WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    attended_row = database.run_query(
        """
        SELECT COUNT(*) AS attended FROM attendance
        WHERE member_id = %s AND (status = 'Present' OR status = 'Late')
        """,
        (member_id,),
        fetch="one"
    )
    missed_row = database.run_query(
        """
        SELECT COUNT(*) AS missed FROM attendance
        WHERE member_id = %s AND status = 'Absent'
        """,
        (member_id,),
        fetch="one"
    )

    total = total_row["total"]
    attended = attended_row["attended"]
    missed = missed_row["missed"]

    if total == 0:
        print("No attendance records for this member yet.")
    else:
        percentage = (attended / total) * 100
        print("Total sessions recorded:", total)
        print("Attended (Present/Late):", attended)
        print("Missed (Absent):", missed)
        print("Attendance percentage:", round(percentage, 1), "%")
    helpers.pause()


def attendance_analytics():
    helpers.print_line("ATTENDANCE ANALYTICS")

    print("\n--- Top 10 most active members ---")
    top_rows = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, COUNT(*) AS times_present
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status = 'Present' OR a.status = 'Late'
        GROUP BY m.member_id, m.first_name, m.last_name
        ORDER BY times_present DESC
        LIMIT 10
        """,
        fetch="all"
    )
    if top_rows == None or len(top_rows) == 0:
        print("No data.")
    else:
        for row in top_rows:
            print(row["first_name"], row["last_name"], "- present/late:", row["times_present"])

    print("\n--- Poor attendance (many Absents) ---")
    poor_rows = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, COUNT(*) AS times_absent
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status = 'Absent'
        GROUP BY m.member_id, m.first_name, m.last_name
        HAVING COUNT(*) >= 2
        ORDER BY times_absent DESC
        """,
        fetch="all"
    )
    if poor_rows == None or len(poor_rows) == 0:
        print("No poor attendance found.")
    else:
        for row in poor_rows:
            print(row["first_name"], row["last_name"], "- absents:", row["times_absent"])

    print("\n--- Perfect attendance ---")
    perfect_rows = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, COUNT(a.attendance_id) AS sessions
        FROM members m
        JOIN attendance a ON m.member_id = a.member_id
        WHERE m.status = 'Active'
        GROUP BY m.member_id, m.first_name, m.last_name
        HAVING SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) = 0
           AND COUNT(a.attendance_id) >= 1
        ORDER BY sessions DESC
        """,
        fetch="all"
    )
    if perfect_rows == None or len(perfect_rows) == 0:
        print("No perfect attendance list yet.")
    else:
        for row in perfect_rows:
            print(row["first_name"], row["last_name"], "- sessions:", row["sessions"])

    print("\n--- 3 or more absences ---")
    consecutive_like = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, COUNT(*) AS absent_count
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status = 'Absent'
        GROUP BY m.member_id, m.first_name, m.last_name
        HAVING COUNT(*) >= 3
        ORDER BY absent_count DESC
        """,
        fetch="all"
    )
    if consecutive_like == None or len(consecutive_like) == 0:
        print("No members with 3 or more absences.")
    else:
        for row in consecutive_like:
            print("Warning:", row["first_name"], row["last_name"], "has", row["absent_count"], "absences.")

    helpers.pause()


def ask_attendance_status(member_label):
    # for village roll call
    print()
    print(">>", member_label)
    print("1=Present  2=Absent  3=Excused  4=Late  5=Skip")
    print("Tip: press Enter = Present")
    choice = input("Status: ").strip()

    if choice == "" or choice == "1":
        return "Present"
    if choice == "2":
        return "Absent"
    if choice == "3":
        return "Excused"
    if choice == "4":
        return "Late"
    if choice == "5":
        return None
    print("Invalid. Skipped.")
    return None


def list_villages():
    rows = database.run_query(
        """
        SELECT village, COUNT(*) AS total
        FROM members
        WHERE status = 'Active'
        GROUP BY village
        ORDER BY village
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No active members / villages found.")
        return []
    print("Villages with active members:")
    for row in rows:
        print("-", row["village"], "(" + str(row["total"]) + " active)")
    return rows


def record_village_or_all_attendance():
    # mark everyone for one official Umuganda Saturday
    helpers.print_line("UMUGANDA ROLL CALL (VILLAGE / ALL MEMBERS)")
    helpers.tip("Choose month only. Date becomes last Saturday automatically.")

    month_info = helpers.ask_umuganda_month()
    if month_info == None:
        helpers.pause()
        return

    attendance_date = month_info[0]
    month_name = month_info[3]
    year = month_info[1]

    activity = helpers.choose_umuganda_remark()
    session_remark = "Umuganda " + month_name + " " + str(year) + " — " + activity

    print()
    print("Who should be marked for this Umuganda?")
    print("1. ALL active members (whole community)")
    print("2. ONE village only")
    scope = input(languages.t("enter_choice")).strip()

    member_rows = None
    scope_label = ""

    if scope == "1":
        member_rows = database.run_query(
            """
            SELECT member_id, first_name, last_name, village, phone
            FROM members
            WHERE status = 'Active'
            ORDER BY village, first_name, last_name
            """,
            fetch="all"
        )
        scope_label = "ALL villages"
    elif scope == "2":
        list_villages()
        village = helpers.get_non_empty("Type village name exactly: ")
        member_rows = database.run_query(
            """
            SELECT member_id, first_name, last_name, village, phone
            FROM members
            WHERE status = 'Active' AND village = %s
            ORDER BY first_name, last_name
            """,
            (village,),
            fetch="all"
        )
        scope_label = village
    else:
        helpers.error(languages.t("invalid_choice"))
        helpers.pause()
        return

    if member_rows == None or len(member_rows) == 0:
        helpers.error("No active members found.")
        helpers.pause()
        return

    print()
    print("Umuganda date:", attendance_date)
    print("Activity:", session_remark)
    print("Recording for:", scope_label)
    print("People:", len(member_rows))
    if helpers.confirm("Start marking now") == False:
        print("Cancelled.")
        helpers.pause()
        return

    saved = 0
    skipped_existing = 0
    skipped_manual = 0

    for row in member_rows:
        existing = database.run_query(
            """
            SELECT attendance_id, status FROM attendance
            WHERE member_id = %s AND attendance_date = %s
            """,
            (row["member_id"], attendance_date),
            fetch="one"
        )
        if existing != None:
            print("Already saved:", row["first_name"], row["last_name"], "->", existing["status"])
            skipped_existing = skipped_existing + 1
            continue

        label = row["first_name"] + " " + row["last_name"] + " | ID " + str(row["member_id"]) + " | " + row["village"]
        status = ask_attendance_status(label)
        if status == None:
            skipped_manual = skipped_manual + 1
            continue

        # personal remark keeps activity + status note
        person_remark = session_remark
        if status == "Late":
            person_remark = session_remark + " | Arrived late"
        elif status == "Excused":
            person_remark = session_remark + " | Excused absence"
        elif status == "Absent":
            person_remark = session_remark + " | Absent"

        result = database.run_query(
            """
            INSERT INTO attendance (member_id, attendance_date, status, remarks)
            VALUES (%s, %s, %s, %s)
            """,
            (row["member_id"], attendance_date, status, person_remark)
        )
        if result != None:
            saved = saved + 1
            print("Saved:", row["first_name"], "as", status)
        else:
            print("Failed for", row["first_name"])

    print()
    print("=== UMUGANDA ROLL CALL DONE ===")
    print("Date:", attendance_date)
    print("Saved:", saved)
    print("Already had record:", skipped_existing)
    print("Skipped:", skipped_manual)
    helpers.pause()


def find_member_for_summary():
    print("Find member by:")
    print("1. Member ID")
    print("2. Phone number")
    choice = input(languages.t("enter_choice")).strip()

    if choice == "1":
        member_id = helpers.get_positive_int("Member ID: ")
        return database.run_query(
            "SELECT * FROM members WHERE member_id = %s",
            (member_id,),
            fetch="one"
        )
    if choice == "2":
        phone = helpers.get_non_empty("Phone number: ")
        return database.run_query(
            "SELECT * FROM members WHERE phone = %s",
            (phone,),
            fetch="one"
        )
    print(languages.t("invalid_choice"))
    return None


def member_lifetime_summary(member=None):
    # if member already logged in we pass the member dict
    helpers.print_line("MEMBER PARTICIPATION SUMMARY (LIFETIME)")

    if member == None:
        print("Find by Member ID or phone.")
        print()
        member = find_member_for_summary()
        if member == None:
            print("Member not found.")
            helpers.pause()
            return

    member_id = member["member_id"]

    print()
    print("=" * 50)
    print("MEMBER:", member["first_name"], member["last_name"])
    print("ID:", member_id, "| Phone:", member["phone"])
    print("Village:", member["village"], "| Cell:", member["cell_name"])
    print("Status:", member["status"], "| Registered:", member["date_registered"])
    print("=" * 50)

    totals = database.run_query(
        """
        SELECT
          COUNT(*) AS total_sessions,
          SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present_count,
          SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) AS late_count,
          SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) AS excused_count,
          SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent_count
        FROM attendance
        WHERE member_id = %s
        """,
        (member_id,),
        fetch="one"
    )

    total = int(totals["total_sessions"] or 0)
    if total == 0:
        print()
        print("No attendance history yet.")
        helpers.pause()
        return

    present = int(totals["present_count"] or 0)
    late = int(totals["late_count"] or 0)
    excused = int(totals["excused_count"] or 0)
    absent = int(totals["absent_count"] or 0)
    attended = present + late
    percentage = (attended / total) * 100

    print()
    print("--- OVERALL ---")
    print("Total sessions:", total)
    print("Present:", present)
    print("Late:", late)
    print("Excused:", excused)
    print("Absent:", absent)
    print("Attended (Present + Late):", attended)
    print("Percentage:", round(percentage, 1), "%")

    dates = database.run_query(
        """
        SELECT MIN(attendance_date) AS first_date, MAX(attendance_date) AS last_date
        FROM attendance WHERE member_id = %s
        """,
        (member_id,),
        fetch="one"
    )
    print("First session:", dates["first_date"])
    print("Last session:", dates["last_date"])

    village_avg = database.run_query(
        """
        SELECT ROUND(
            100 * SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) / COUNT(*), 1
        ) AS village_pct
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE m.village = %s
        """,
        (member["village"],),
        fetch="one"
    )
    if village_avg != None and village_avg["village_pct"] != None:
        print("Village average:", village_avg["village_pct"], "%")
        if percentage >= float(village_avg["village_pct"]):
            print("You are at or above village average.")
        else:
            print("You are below village average.")

    print()
    print("--- HISTORY ---")
    history = database.run_query(
        """
        SELECT attendance_date, status, remarks
        FROM attendance WHERE member_id = %s
        ORDER BY attendance_date DESC
        """,
        (member_id,),
        fetch="all"
    )
    for row in history:
        extra = ""
        if row["remarks"] != None:
            extra = " | " + row["remarks"]
        print(row["attendance_date"], "-", row["status"] + extra)

    print()
    print("--- ABSENT DATES ---")
    absents = database.run_query(
        """
        SELECT attendance_date FROM attendance
        WHERE member_id = %s AND status = 'Absent'
        ORDER BY attendance_date DESC
        """,
        (member_id,),
        fetch="all"
    )
    if absents == None or len(absents) == 0:
        print("No absences.")
    else:
        for row in absents:
            print("-", row["attendance_date"])

    helpers.pause()


def member_own_history(member):
    helpers.print_line("MY ATTENDANCE HISTORY")
    rows = database.run_query(
        """
        SELECT attendance_date, status, remarks
        FROM attendance WHERE member_id = %s
        ORDER BY attendance_date DESC
        """,
        (member["member_id"],),
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No attendance records yet.")
    else:
        for row in rows:
            extra = ""
            if row["remarks"] != None:
                extra = " | " + row["remarks"]
            print(row["attendance_date"], "-", row["status"] + extra)
    helpers.pause()

