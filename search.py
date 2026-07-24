# search.py
# Owner: Friend
# search members, projects, tools, attendance date

import database
import helpers
import languages


def search_menu():
    running = True
    while running:
        helpers.print_line(languages.t("search_menu"))
        print(languages.t("s1"))
        print(languages.t("s2"))
        print(languages.t("s3"))
        print(languages.t("s4"))
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
        elif choice == "0":
            running = False
        else:
            print(languages.t("invalid_choice"))


def search_members():
    text = helpers.get_non_empty("Type Member ID, name, or phone: ")
    like_text = "%" + text + "%"

    if text.isdigit():
        rows = database.run_query(
            """
            SELECT * FROM members
            WHERE member_id = %s OR phone LIKE %s
               OR first_name LIKE %s OR last_name LIKE %s
            """,
            (int(text), like_text, like_text, like_text),
            fetch="all"
        )
    else:
        rows = database.run_query(
            """
            SELECT * FROM members
            WHERE phone LIKE %s OR first_name LIKE %s OR last_name LIKE %s
            """,
            (like_text, like_text, like_text),
            fetch="all"
        )

    if rows == None or len(rows) == 0:
        print("No members found.")
    else:
        for row in rows:
            print(row["member_id"], row["first_name"], row["last_name"], row["phone"], row["status"])
    helpers.pause()


def search_projects():
    name = helpers.get_non_empty("Project name contains: ")
    like_name = "%" + name + "%"
    rows = database.run_query(
        """
        SELECT project_id, project_name, status, percent_complete, location
        FROM projects
        WHERE project_name LIKE %s
        """,
        (like_name,),
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No projects found.")
    else:
        for row in rows:
            print(row["project_id"], row["project_name"], row["status"], str(row["percent_complete"]) + "%", row["location"])
    helpers.pause()


def search_tools():
    name = helpers.get_non_empty("Tool name contains: ")
    like_name = "%" + name + "%"
    rows = database.run_query(
        """
        SELECT tool_id, tool_name, available_quantity, total_quantity, condition_status
        FROM tools
        WHERE tool_name LIKE %s
        """,
        (like_name,),
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No tools found.")
    else:
        for row in rows:
            print(row["tool_id"], row["tool_name"], row["available_quantity"], "/", row["total_quantity"], row["condition_status"])
    helpers.pause()


def search_attendance_date():
    helpers.tip("Choose month. System uses last Saturday of that month.")
    month_info = helpers.ask_umuganda_month()
    if month_info == None:
        helpers.pause()
        return
    the_date = month_info[0]
    rows = database.run_query(
        """
        SELECT a.attendance_date, a.status, a.remarks, m.first_name, m.last_name
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        WHERE a.attendance_date = %s
        ORDER BY m.first_name
        """,
        (the_date,),
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No attendance on that Umuganda date.")
    else:
        for row in rows:
            print(
                row["attendance_date"],
                row["first_name"], row["last_name"],
                row["status"], "|", row["remarks"]
            )
    helpers.pause()
