# notifications.py
# warnings for the village leader

from datetime import datetime
import database
import helpers
import tools
import projects
import languages


def show_notifications():
    print(languages.t("notifications"))
    found = False

    low_count = tools.count_low_stock_tools()
    if low_count > 0:
        found = True
        msg = languages.t("warn_low_stock")
        msg = msg.replace("{n}", str(low_count))
        print(msg)

    overdue_names = projects.list_overdue_project_names()
    i = 0
    while i < len(overdue_names):
        found = True
        msg = languages.t("warn_overdue")
        msg = msg.replace("{name}", overdue_names[i])
        print(msg)
        i = i + 1

    # check attendance for THIS MONTH's official Umuganda (last Saturday)
    now = datetime.now()
    umuganda = helpers.get_last_saturday(now.year, now.month)
    umuganda_text = umuganda.strftime("%Y-%m-%d")
    month_name = helpers.MONTH_NAMES[now.month]

    umuganda_row = database.run_query(
        "SELECT COUNT(*) AS total FROM attendance WHERE attendance_date = %s",
        (umuganda_text,),
        fetch="one"
    )
    if umuganda_row != None:
        if umuganda_row["total"] == 0:
            found = True
            print(
                "Notice: No attendance recorded for this month's Umuganda (",
                umuganda_text,
                "-",
                month_name + ")."
            )
        else:
            absent_row = database.run_query(
                """
                SELECT COUNT(*) AS total FROM attendance
                WHERE attendance_date = %s AND status = 'Absent'
                """,
                (umuganda_text,),
                fetch="one"
            )
            if absent_row != None and absent_row["total"] > 0:
                found = True
                print(
                    "Notice:",
                    absent_row["total"],
                    "member(s) were Absent on Umuganda",
                    umuganda_text + "."
                )

    latest = database.run_query(
        "SELECT MAX(attendance_date) AS latest_date FROM attendance",
        fetch="one"
    )
    if latest != None and latest["latest_date"] != None:
        print("Latest Umuganda on record:", latest["latest_date"])

    if found == False:
        print(languages.t("no_warnings"))
    print()
