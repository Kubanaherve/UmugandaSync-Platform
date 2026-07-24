# dashboard.py
# Village Leader home numbers (live from MySQL)

import database
import helpers
import tools
import projects
import languages


def show_dashboard(admin_name):
    helpers.print_line(languages.t("dashboard") + admin_name)

    total_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members",
        fetch="one"
    )
    active_members = database.run_query(
        "SELECT COUNT(*) AS total FROM members WHERE status='Active'",
        fetch="one"
    )

    today = helpers.today_string()
    today_attendance = database.run_query(
        "SELECT COUNT(*) AS total FROM attendance WHERE attendance_date = %s",
        (today,),
        fetch="one"
    )

    ongoing = database.run_query(
        "SELECT COUNT(*) AS total FROM projects WHERE status='Ongoing'",
        fetch="one"
    )

    available_tools = database.run_query(
        "SELECT SUM(available_quantity) AS total FROM tools",
        fetch="one"
    )

    low_stock = tools.count_low_stock_tools()
    overdue = projects.count_overdue_projects()

    print(languages.t("total_members"), total_members["total"])
    print(languages.t("active_members"), active_members["total"])
    print(languages.t("today_attendance"), today_attendance["total"], "(" + today + ")")
    print(languages.t("ongoing_projects"), ongoing["total"])

    if available_tools["total"] == None:
        print(languages.t("available_tools"), 0)
    else:
        print(languages.t("available_tools"), available_tools["total"])

    print(languages.t("low_stock_tools"), low_stock)
    print(languages.t("overdue_projects"), overdue)

    # official Umuganda date for current month (last Saturday)
    from datetime import datetime
    now = datetime.now()
    umuganda = helpers.get_last_saturday(now.year, now.month)
    print(
        "THIS MONTH UMUGANDA:",
        umuganda.strftime("%Y-%m-%d"),
        "(last Saturday of " + helpers.MONTH_NAMES[now.month] + ")"
    )

    if low_stock > 0 or overdue > 0:
        print()
        helpers.tip("Open Attendance / Projects / Tools / Reports for details.")
    print()
