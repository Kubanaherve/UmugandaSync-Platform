"""
reports.py
Owner: Marvella
reports and stats for village leader

Generates community, member, attendance, project, and inventory reports
for the village leader, plus file exports for select reports.

"""

import csv
import database
import helpers
import languages
from datetime import datetime

def safe_num(value):
    # returns 0 instead of None so counts/sums never crash on empty tables
    if value is None:
        return 0
    return value

def make_export_filename(prefix, extension="txt"):
    # builds a timestamped filename so repeated exports don't overwrite each other
    return prefix + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "." + extension

def reports_menu():
    running = True
    while running == True:
        helpers.print_line(languages.t("reports_menu"))
        print(languages.t("r1"))
        print(languages.t("r2"))
        print(languages.t("r3"))
        print(languages.t("r4"))
        print(languages.t("r5"))
        print(languages.t("r6"))
        print(languages.t("r7"))
        print(languages.t("r8"))
        print("9. Export Community Summary to File")
        print("10. Export Project Summary to File")
        print("11. Export Community Summary to CSV")
        print(languages.t("r0"))
        choice = input(languages.t("enter_choice")).strip()

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
            export_community_summary_csv()
        elif choice == "0":
            print("Returning to main menu...")
            running = False
        else:
            print("Invalid choice.")


def community_summary():
    # big picture numbers
    helpers.print_line("COMMUNITY SUMMARY")

    total_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members", fetch="one"
    )
    active_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one"
    )
    total_projects = database.run_query(
        "SELECT COUNT(*) AS total FROM projects", fetch="one"
    )
    ongoing = database.run_query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'",
        fetch="one"
    )
    total_tools = database.run_query(
        "SELECT COUNT(*) AS total FROM tools", fetch="one"
    )
    available_tools = database.run_query(
        "SELECT SUM(available_quantity) AS total FROM tools", fetch="one"
    )
    attendance_days = database.run_query(
        "SELECT COUNT(DISTINCT attendance_date) AS total FROM attendance",
        fetch="one"
    )

    print("Total members:", safe_num(total_members["total"]))
    print("Active members:", safe_num(active_members["total"]))
    print("Total projects:", safe_num(total_projects["total"]))
    print("Ongoing projects:", safe_num(ongoing["total"]))
    print("Tool types:", safe_num(total_tools["total"]))
    print("Available tool units:", safe_num(available_tools["total"]))
    print("Umuganda dates recorded:", safe_num(attendance_days["total"]))
    helpers.pause()

def export_community_summary():
    # writes the same numbers as community_summary(), but to a file
    helpers.print_line("EXPORT COMMUNITY SUMMARY")

    total_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members", fetch="one"
    )
    active_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one"
    )
    total_projects = database.run_query(
        "SELECT COUNT(*) AS total FROM projects", fetch="one"
    )
    ongoing = database.run_query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'",
        fetch="one"
    )
    total_tools = database.run_query(
        "SELECT COUNT(*) AS total FROM tools", fetch="one"
    )
    available_tools = database.run_query(
        "SELECT SUM(available_quantity) AS total FROM tools", fetch="one"
    )
    attendance_days = database.run_query(
        "SELECT COUNT(DISTINCT attendance_date) AS total FROM attendance",
        fetch="one"
    )


    filename = make_export_filename("community_summary")

    with open(filename, "w") as f:
        f.write("COMMUNITY SUMMARY\n")
        f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n")
        f.write("Total members: " + str(safe_num(total_members["total"])) + "\n")
        f.write("Active members: " + str(safe_num(active_members["total"])) + "\n")
        f.write("Total projects: " + str(safe_num(total_projects["total"])) + "\n")
        f.write("Ongoing projects: " + str(safe_num(ongoing["total"])) + "\n")
        f.write("Tool types: " + str(safe_num(total_tools["total"])) + "\n")
        f.write("Available tool units: " + str(safe_num(available_tools["total"])) + "\n")
        f.write("Umuganda dates recorded: " + str(safe_num(attendance_days["total"])) + "\n")

    print("Exported to", filename)
    helpers.pause()

def export_community_summary_csv():
    # same community summary numbers, but as a CSV file (one metric per row)
    total_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members", fetch="one"
    )
    active_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one"
    )
    total_projects = database.run_query(
        "SELECT COUNT(*) AS total FROM projects", fetch="one"
    )
    ongoing = database.run_query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'",
        fetch="one"
    )
    total_tools = database.run_query(
        "SELECT COUNT(*) AS total FROM tools", fetch="one"
    )
    available_tools = database.run_query(
        "SELECT SUM(available_quantity) AS total FROM tools", fetch="one"
    )
    attendance_days = database.run_query(
        "SELECT COUNT(DISTINCT attendance_date) AS total FROM attendance",
        fetch="one"
    )

    filename = make_export_filename("community_summary", "csv")

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total members", safe_num(total_members["total"])])
        writer.writerow(["Active members", safe_num(active_members["total"])])
        writer.writerow(["Total projects", safe_num(total_projects["total"])])
        writer.writerow(["Ongoing projects", safe_num(ongoing["total"])])
        writer.writerow(["Tool types", safe_num(total_tools["total"])])
        writer.writerow(["Available tool units", safe_num(available_tools["total"])])
        writer.writerow(["Umuganda dates recorded", safe_num(attendance_days["total"])])

    print("Exported to", filename)
    helpers.pause()

def member_report():
    # members by status and village
    helpers.print_line("MEMBER REPORT")

    print("\n--- By status ---")
    rows = database.run_query(
        """
        SELECT status, COUNT(*) AS total
        FROM members
        GROUP BY status
        ORDER BY status
        """,
        fetch="all"
    )
    if rows != None:
        for row in rows:
            print(row["status"] + ":", row["total"])

    print("\n--- By village ---")
    rows2 = database.run_query(
        """
        SELECT village, COUNT(*) AS total
        FROM members
        GROUP BY village
        ORDER BY total DESC
        """,
        fetch="all"
    )
    if rows2 is not None:
        for row in rows2:
            print(row["village"] + ":", row["total"])
    helpers.pause()


def attendance_summary():
    helpers.print_line("ATTENDANCE SUMMARY")
    rows = database.run_query(
        """
        SELECT status, COUNT(*) AS total
        FROM attendance
        GROUP BY status
        ORDER BY total DESC
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No attendance data.")
    else:
        for row in rows:
            print(row["status"] + ":", row["total"])

    avg_row = database.run_query(
        """
        SELECT
          ROUND(
            100 * SUM(CASE WHEN status IN ('Present','Late') THEN 1 ELSE 0 END)
            / COUNT(*), 1
          ) AS avg_present_pct
        FROM attendance
        """,
        fetch="one"
    )
    if avg_row != None and avg_row["avg_present_pct"] != None:
        print("Overall present/late rate:", avg_row["avg_present_pct"], "%")
    else:
        print("Overall present/late rate: N/A (no attendance data yet)")
    helpers.pause()


def most_active_members():
    # top 10 by present/late
    helpers.print_line("MOST ACTIVE MEMBERS")
    rows = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, m.village,
               COUNT(*) AS active_count
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status IN ('Present', 'Late')
        GROUP BY m.member_id, m.first_name, m.last_name, m.village
        ORDER BY active_count DESC
        LIMIT 10
        """,
        fetch="all"
    )
    if rows is None or len(rows) == 0:
        print("No data.")
    else:
        for row in rows:
            print(
                row["first_name"], row["last_name"],
                "(" + row["village"] + ") -",
                row["active_count"], "present/late"
            )
    helpers.pause()


def poor_attendance_members():
    # members with 2+ absences
    helpers.print_line("POOR ATTENDANCE")
    rows = database.run_query(
        """
        SELECT m.member_id, m.first_name, m.last_name, m.phone,
               COUNT(*) AS absent_count
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.status = 'Absent'
        GROUP BY m.member_id, m.first_name, m.last_name, m.phone
        HAVING COUNT(*) >= 2
        ORDER BY absent_count DESC
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No poor attendance found.")
    else:
        for row in rows:
            print(
                row["first_name"], row["last_name"],
                "| phone:", row["phone"],
                "| absents:", row["absent_count"]
            )
    helpers.pause()


def project_summary():
    # projects grouped by status
    helpers.print_line("PROJECT SUMMARY")
    rows = database.run_query(
        """
        SELECT status, COUNT(*) AS total,
               ROUND(AVG(percent_complete), 1) AS avg_progress
        FROM projects
        GROUP BY status
        ORDER BY status
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No projects.")
    else:
        for row in rows:
            print(
                row["status"] + ":", row["total"],
                "projects | avg progress:", row["avg_progress"], "%"
            )

    print("\n--- Incomplete projects ---")
    incomplete = database.run_query(
        """
        SELECT project_name, status, percent_complete, expected_end_date
        FROM projects
        WHERE status IN ('Pending', 'Ongoing')
        ORDER BY expected_end_date
        """,
        fetch="all"
    )
    if incomplete != None:
        for row in incomplete:
            print(
                row["project_name"], "|", row["status"], "|",
                str(row["percent_complete"]) + "% | due",
                row["expected_end_date"]
            )
    helpers.pause()

def export_project_summary():
    # writes the incomplete-projects list to a file, like project_summary() does on screen
    helpers.print_line("EXPORT PROJECT SUMMARY")

    rows = database.run_query(
        """
        SELECT status, COUNT(*) AS total,
               ROUND(AVG(percent_complete), 1) AS avg_progress
        FROM projects
        GROUP BY status
        ORDER BY status
        """,
        fetch="all"
    )

    incomplete = database.run_query(
        """
        SELECT project_name, status, percent_complete, expected_end_date
        FROM projects
        WHERE status IN ('Pending', 'Ongoing')
        ORDER BY expected_end_date
        """,
        fetch="all"
    )

    from datetime import datetime
    filename = "project_summary_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"

    with open(filename, "w") as f:
        f.write("PROJECT SUMMARY\n")
        f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n")

        if rows == None or len(rows) == 0:
            f.write("No projects.\n")
        else:
            for row in rows:
                f.write(
                    row["status"] + ": " + str(row["total"]) +
                    " projects | avg progress: " + str(row["avg_progress"]) + "%\n"
                )

        f.write("\n--- Incomplete projects ---\n")
        if incomplete == None or len(incomplete) == 0:
            f.write("None\n")
        else:
            for row in incomplete:
                f.write(
                    row["project_name"] + " | " + row["status"] + " | " +
                    str(row["percent_complete"]) + "% | due " +
                    str(row["expected_end_date"]) + "\n"
                )

    print("Exported to", filename)
    helpers.pause()

def inventory_summary():
    # tool stock report
    helpers.print_line("INVENTORY SUMMARY")
    totals = database.run_query(
        """
        SELECT
          COUNT(*) AS tool_types,
          SUM(total_quantity) AS total_units,
          SUM(available_quantity) AS available_units
        FROM tools
        """,
        fetch="one"
    )
    if totals is not None:
        print("Tool types:", totals["tool_types"])
        print("Total units:", totals["total_units"])
        print("Available units:", totals["available_units"])

    print("\n--- By condition ---")
    by_cond = database.run_query(
        """
        SELECT condition_status, COUNT(*) AS total
        FROM tools
        GROUP BY condition_status
        """,
        fetch="all"
    )
    if by_cond != None:
        for row in by_cond:
            print(row["condition_status"] + ":", row["total"])

    print("\n--- Low stock ---")
    low = database.run_query(
        """
        SELECT tool_name, available_quantity, low_stock_limit
        FROM tools
        WHERE available_quantity <= low_stock_limit
        ORDER BY available_quantity
        """,
        fetch="all"
    )
    if low == None or len(low) == 0:
        print("None")
    else:
        for row in low:
            print(
                row["tool_name"], ":",
                row["available_quantity"], "left"
            )

    print("\n--- Currently borrowed ---")
    borrowed = database.run_query(
        """
        SELECT t.tool_name, m.first_name, m.last_name, b.quantity, b.borrow_date
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        JOIN members m ON b.member_id = m.member_id
        WHERE b.status = 'Borrowed'
        ORDER BY b.borrow_date
        """,
        fetch="all"
    )
    if borrowed is None or len(borrowed) == 0:
        print("No open borrows.")
    else:
        for row in borrowed:
            print(
                row["tool_name"], "x", row["quantity"],
                "->", row["first_name"], row["last_name"],
                "since", row["borrow_date"]
            )
    helpers.pause()


def attendance_by_village():
    # attendance per village
    helpers.print_line("ATTENDANCE BY VILLAGE")
    rows = database.run_query(
        """
        SELECT m.village,
               COUNT(*) AS records,
               SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END)
                 AS present_like,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absents
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        GROUP BY m.village
        ORDER BY present_like DESC
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No data.")
    else:
        for row in rows:
            print(
                row["village"],
                "| records:", row["records"],
                "| present/late:", row["present_like"],
                "| absent:", row["absents"]
            )
    helpers.pause()
