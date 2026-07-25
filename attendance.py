# attendance.py
# Attendance management for UmugandaSync

from datetime import datetime
import database
import helpers
import languages


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
            record_whole_village()
        elif choice == "9":
            member_participation_summary()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


def record_attendance():
    helpers.print_line(languages.t("a1"))
    member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
    member = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if member is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return
    if member["status"] != "Active":
        helpers.error(languages.t("member_inactive_attendance"))
        helpers.pause()
        return

    print(languages.t("member") + ":", member["first_name"], member["last_name"],
          "|", member["village"])

    today = helpers.today_string()
    existing = database.run_query(
        "SELECT * FROM attendance WHERE member_id = %s AND attendance_date = %s",
        (member_id, today),
        fetch="one"
    )
    if existing is not None:
        helpers.error(languages.t("attendance_exists_today"))
        helpers.pause()
        return

    print()
    print(languages.t("attendance_status_prompt"))
    print("1. Present")
    print("2. Late")
    print("3. Absent")
    print("4. Excused")
    status_choice = input(languages.t("enter_choice")).strip()
    status_map = {"1": "Present", "2": "Late", "3": "Absent", "4": "Excused"}
    status = status_map.get(status_choice)
    if status is None:
        helpers.error(languages.t("invalid_choice"))
        helpers.pause()
        return

    remark = helpers.choose_umuganda_remark()
    if status == "Absent":
        remark = remark + " | Absent"
    elif status == "Late":
        remark = remark + " | Arrived late"
    elif status == "Excused":
        remark = remark + " | Excused absence"

    sql = """
        INSERT INTO attendance (member_id, attendance_date, status, remarks)
        VALUES (%s, %s, %s, %s)
    """
    result = database.run_query(sql, (member_id, today, status, remark))
    if result is not None:
        helpers.success(languages.t("attendance_recorded"))
    else:
        helpers.error(languages.t("attendance_record_failed"))
    helpers.pause()


def view_all_attendance():
    helpers.print_line(languages.t("a2"))
    rows = database.run_query(
        """
        SELECT a.*, m.first_name, m.last_name, m.village
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        ORDER BY a.attendance_date DESC, m.first_name
        LIMIT 100
        """,
        fetch="all"
    )
    _display_attendance(rows)
    helpers.pause()


def view_by_date():
    helpers.print_line(languages.t("a3"))
    date_text = helpers.get_date(languages.t("date_prompt_text"))
    rows = database.run_query(
        """
        SELECT a.*, m.first_name, m.last_name, m.village
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.attendance_date = %s
        ORDER BY m.village, m.first_name
        """,
        (date_text,),
        fetch="all"
    )
    _display_attendance(rows)
    helpers.pause()


def view_by_member():
    helpers.print_line(languages.t("a4"))
    member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
    member = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if member is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return

    print(languages.t("member") + ":", member["first_name"], member["last_name"])
    print()
    rows = database.run_query(
        """
        SELECT * FROM attendance
        WHERE member_id = %s
        ORDER BY attendance_date DESC
        """,
        (member_id,),
        fetch="all"
    )
    if not rows:
        print(languages.t("no_attendance"))
    else:
        for row in rows:
            print(row["attendance_date"], "|", row["status"].ljust(10), "|", row["remarks"])
    helpers.pause()


def search_attendance():
    helpers.print_line(languages.t("a5"))
    term = helpers.get_non_empty(languages.t("search_term_prompt"))
    like_term = "%" + term + "%"
    rows = database.run_query(
        """
        SELECT a.*, m.first_name, m.last_name, m.village
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE m.first_name LIKE %s OR m.last_name LIKE %s
           OR a.remarks LIKE %s OR a.status LIKE %s
        ORDER BY a.attendance_date DESC
        LIMIT 50
        """,
        (like_term, like_term, like_term, like_term),
        fetch="all"
    )
    _display_attendance(rows)
    helpers.pause()


def member_attendance_percentage():
    helpers.print_line(languages.t("a6"))
    member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
    member = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if member is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return

    row = database.run_query(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS present_late
        FROM attendance
        WHERE member_id = %s
        """,
        (member_id,),
        fetch="one"
    )
    if row is None or row["total"] == 0:
        print(languages.t("member") + ":", member["first_name"], member["last_name"])
        print(languages.t("no_attendance_data"))
    else:
        pct = round(100.0 * row["present_late"] / row["total"], 1)
        print(languages.t("member") + ":", member["first_name"], member["last_name"])
        print(languages.t("attendance_rate") + ":", str(pct) + "%",
              "(" + str(row["present_late"]) + "/" + str(row["total"]) + ")")
    helpers.pause()


def attendance_analytics():
    helpers.print_line(languages.t("a7"))
    print("--- " + languages.t("a7") + " ---")
    print()

    total_active = database.run_query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one"
    )
    all_attendance = database.run_query(
        "SELECT COUNT(DISTINCT member_id) AS total FROM attendance",
        fetch="one"
    )
    active_count = total_active["total"] if total_active else 0
    attended_count = all_attendance["total"] if all_attendance else 0

    print(languages.t("active_members") + " " + str(active_count))
    print(languages.t("ever_attended") + " " + str(attended_count))
    never = active_count - attended_count
    if never > 0:
        helpers.tip(str(never) + " " + languages.t("never_attended_tip"))
    print()

    poor = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, COUNT(*) AS absences
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status = 'Absent'
        GROUP BY m.member_id, m.first_name, m.last_name
        HAVING COUNT(*) >= 3
        ORDER BY absences DESC
        """,
        fetch="all"
    )
    if poor:
        print(languages.t("members_3_absences") + ":")
        for row in poor:
            print("  -", row["first_name"], row["last_name"],
                  "(" + str(row["absences"]) + " " + languages.t("absences_lc") + ")")
    else:
        print(languages.t("no_poor_attendance"))

    helpers.pause()


def record_whole_village():
    helpers.print_line(languages.t("a8"))
    print(languages.t("a8_help"))
    ok = helpers.confirm(languages.t("continue_question"))
    if not ok:
        return

    today = helpers.today_string()
    active_members = database.run_query(
        "SELECT * FROM members WHERE status='Active'",
        fetch="all"
    )
    if not active_members:
        helpers.error(languages.t("no_active_members"))
        helpers.pause()
        return

    print()
    print(languages.t("attendance_status_prompt"))
    print("1. Present")
    print("2. Late")
    print("3. Absent")
    print("4. Excused")
    default_choice = input(languages.t("default_status_prompt")).strip()
    default_status = {"1": "Present", "2": "Late", "3": "Absent", "4": "Excused"}.get(default_choice, "Present")

    remark = helpers.choose_umuganda_remark()

    recorded = 0
    skipped = 0
    for m in active_members:
        existing = database.run_query(
            "SELECT attendance_id FROM attendance WHERE member_id = %s AND attendance_date = %s",
            (m["member_id"], today),
            fetch="one"
        )
        if existing is None:
            full_remark = remark
            if default_status == "Absent":
                full_remark = remark + " | Absent"
            elif default_status == "Late":
                full_remark = remark + " | Arrived late"
            elif default_status == "Excused":
                full_remark = remark + " | Excused absence"
            database.run_query(
                "INSERT INTO attendance (member_id, attendance_date, status, remarks) VALUES (%s, %s, %s, %s)",
                (m["member_id"], today, default_status, full_remark)
            )
            recorded = recorded + 1
        else:
            skipped = skipped + 1

    helpers.success(
        languages.t("village_recorded") + " " + str(recorded) +
        " (" + str(skipped) + " " + languages.t("already_recorded") + ")"
    )
    helpers.pause()


def member_participation_summary():
    helpers.print_line(languages.t("a9"))
    member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
    member = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if member is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return

    member_lifetime_summary(member)
    helpers.pause()


def member_lifetime_summary(member):
    name = member["first_name"] + " " + member["last_name"]
    helpers.print_line(languages.t("member_summary") + " - " + name)
    print("  " + languages.t("village") + ":", member["village"],
          "| " + languages.t("status") + ":", member["status"])

    rows = database.run_query(
        "SELECT * FROM attendance WHERE member_id = %s ORDER BY attendance_date",
        (member["member_id"],),
        fetch="all"
    )

    if not rows:
        print("  " + languages.t("no_attendance_recorded"))
        print()
        return

    total = len(rows)
    present = sum(1 for r in rows if r["status"] == "Present")
    late = sum(1 for r in rows if r["status"] == "Late")
    absent = sum(1 for r in rows if r["status"] == "Absent")
    excused = sum(1 for r in rows if r["status"] == "Excused")
    rate = round(100.0 * (present + late) / total, 1)

    print()
    print("  " + languages.t("total_sessions") + ":", total)
    print("  " + languages.t("present") + ":", present)
    print("  " + languages.t("late") + ":", late)
    print("  " + languages.t("absent") + ":", absent)
    print("  " + languages.t("excused") + ":", excused)
    print("  " + languages.t("attendance_rate") + ":", str(rate) + "%")
    print()


def member_own_history(member):
    rows = database.run_query(
        "SELECT * FROM attendance WHERE member_id = %s ORDER BY attendance_date DESC",
        (member["member_id"],),
        fetch="all"
    )
    if not rows:
        print(languages.t("no_attendance_recorded"))
        return
    for r in rows:
        print("  " + r["attendance_date"] + " | " + r["status"].ljust(10) + " | " + (r["remarks"] or ""))


def _display_attendance(rows):
    if not rows:
        print(languages.t("no_attendance"))
        return
    for r in rows:
        print(
            r["attendance_date"],
            "|", r["first_name"].ljust(15), r["last_name"].ljust(15),
            "|", r["village"].ljust(12),
            "|", r["status"].ljust(10),
            "|", r["remarks"] or ""
        )
    print()
    print(languages.t("total") + ":", len(rows))
