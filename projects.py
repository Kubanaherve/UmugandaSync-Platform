# projects.py
# Project management for UmugandaSync

from datetime import datetime
import database
import helpers
import languages


def project_menu():
    running = True
    while running:
        helpers.print_line(languages.t("project_menu"))
        print(languages.t("p1"))
        print(languages.t("p2"))
        print(languages.t("p3"))
        print(languages.t("p4"))
        print(languages.t("p5"))
        print(languages.t("p6"))
        print(languages.t("p7"))
        print(languages.t("p8"))
        print(languages.t("p9"))
        print(languages.t("p0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            register_project()
        elif choice == "2":
            view_all_projects()
        elif choice == "3":
            view_projects_by_status("Ongoing")
        elif choice == "4":
            view_projects_by_status("Completed")
        elif choice == "5":
            view_overdue_projects()
        elif choice == "6":
            search_projects()
        elif choice == "7":
            update_project_progress()
        elif choice == "8":
            mark_project_completed()
        elif choice == "9":
            delete_project()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


def register_project():
    helpers.print_line(languages.t("p1"))
    project_name = helpers.get_non_empty(languages.t("project_name_prompt"))
    description = input(languages.t("project_desc_prompt")).strip()
    location = helpers.get_non_empty(languages.t("project_location_prompt"))
    leader = helpers.get_positive_int(languages.t("project_leader_prompt"))
    start_date = helpers.get_date(languages.t("project_start_prompt"))
    end_date = helpers.get_date(languages.t("project_end_prompt"))

    leader_check = database.run_query(
        "SELECT member_id FROM members WHERE member_id = %s",
        (leader,),
        fetch="one"
    )
    if leader_check is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return

    sql = """
        INSERT INTO projects
        (project_name, description, location, leader_member_id,
         start_date, expected_end_date, status, percent_complete)
        VALUES (%s, %s, %s, %s, %s, %s, 'Pending', 0)
    """
    result = database.run_query(sql, (project_name, description, location, leader, start_date, end_date))
    if result is not None:
        helpers.success(languages.t("project_added") + " (ID: " + str(result) + ")")
    else:
        helpers.error(languages.t("project_add_failed"))
    helpers.pause()


def view_all_projects():
    helpers.print_line(languages.t("p2"))
    rows = database.run_query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        ORDER BY p.start_date DESC
        """,
        fetch="all"
    )
    _display_projects(rows)
    helpers.pause()


def view_projects_by_status(status):
    label = {"Ongoing": languages.t("p3"), "Completed": languages.t("p4")}
    helpers.print_line(label.get(status, status))
    rows = database.run_query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.status = %s
        ORDER BY p.start_date DESC
        """,
        (status,),
        fetch="all"
    )
    _display_projects(rows)
    helpers.pause()


def view_overdue_projects():
    helpers.print_line(languages.t("p5"))
    today = helpers.today_string()
    rows = database.run_query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.status IN ('Pending', 'Ongoing')
          AND p.expected_end_date < %s
        ORDER BY p.expected_end_date
        """,
        (today,),
        fetch="all"
    )
    _display_projects(rows)
    helpers.pause()


def search_projects():
    helpers.print_line(languages.t("p6"))
    name = helpers.get_non_empty(languages.t("search_term_prompt"))
    like_name = "%" + name + "%"
    rows = database.run_query(
        """
        SELECT p.*, m.first_name, m.last_name
        FROM projects p
        LEFT JOIN members m ON p.leader_member_id = m.member_id
        WHERE p.project_name LIKE %s OR p.location LIKE %s
        ORDER BY p.project_name
        """,
        (like_name, like_name),
        fetch="all"
    )
    _display_projects(rows)
    helpers.pause()


def update_project_progress():
    helpers.print_line(languages.t("p7"))
    project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
    project = database.run_query(
        "SELECT * FROM projects WHERE project_id = %s",
        (project_id,),
        fetch="one"
    )
    if project is None:
        helpers.error(languages.t("project_not_found"))
        helpers.pause()
        return

    print(languages.t("current_values") + ":")
    print("  ", project["project_name"], "|",
          project["status"], "|",
          str(project["percent_complete"]) + "%",
          "|", languages.t("due"), project["expected_end_date"])

    percent = helpers.get_int_in_range(
        languages.t("progress_prompt") + " (0-100): ", 0, 100
    )

    new_status = project["status"]
    if percent == 100:
        new_status = "Completed"
    elif percent > 0 and project["status"] == "Pending":
        new_status = "Ongoing"

    result = database.run_query(
        "UPDATE projects SET percent_complete=%s, status=%s WHERE project_id=%s",
        (percent, new_status, project_id)
    )
    if result is not None:
        helpers.success(languages.t("project_updated"))
    else:
        helpers.error(languages.t("project_update_failed"))
    helpers.pause()


def mark_project_completed():
    helpers.print_line(languages.t("p8"))
    project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
    project = database.run_query(
        "SELECT * FROM projects WHERE project_id = %s",
        (project_id,),
        fetch="one"
    )
    if project is None:
        helpers.error(languages.t("project_not_found"))
        helpers.pause()
        return

    print(languages.t("mark_complete") + ":", project["project_name"])
    ok = helpers.confirm(languages.t("are_you_sure"))
    if ok:
        result = database.run_query(
            "UPDATE projects SET status='Completed', percent_complete=100 WHERE project_id=%s",
            (project_id,)
        )
        if result is not None:
            helpers.success(languages.t("project_completed"))
        else:
            helpers.error(languages.t("project_complete_failed"))
    helpers.pause()


def delete_project():
    helpers.print_line(languages.t("p9"))
    project_id = helpers.get_positive_int(languages.t("project_id_prompt"))
    project = database.run_query(
        "SELECT * FROM projects WHERE project_id = %s",
        (project_id,),
        fetch="one"
    )
    if project is None:
        helpers.error(languages.t("project_not_found"))
        helpers.pause()
        return

    print(languages.t("confirm_delete") + ":", project["project_name"])
    ok = helpers.confirm(languages.t("are_you_sure"))
    if ok:
        result = database.run_query("DELETE FROM projects WHERE project_id = %s", (project_id,))
        if result is not None:
            helpers.success(languages.t("project_deleted"))
        else:
            helpers.error(languages.t("project_delete_failed"))
    helpers.pause()


def _display_projects(rows):
    if not rows:
        print(languages.t("no_projects"))
        return
    for row in rows:
        leader = (row["first_name"] or "") + " " + (row["last_name"] or "")
        if leader.strip() == "":
            leader = languages.t("no_leader")
        print(
            "P#" + str(row["project_id"]).rjust(3),
            row["project_name"].ljust(30),
            "|", row["status"].ljust(12),
            "|", str(row["percent_complete"]).rjust(3) + "%",
            "|", languages.t("due"), row["expected_end_date"],
            "|", languages.t("leader") + ":", leader
        )
    print()
    print(languages.t("total") + ":", len(rows))


def count_overdue_projects():
    today = helpers.today_string()
    row = database.run_query(
        """
        SELECT COUNT(*) AS total FROM projects
        WHERE status IN ('Pending', 'Ongoing')
          AND expected_end_date < %s
        """,
        (today,),
        fetch="one"
    )
    if row is None:
        return 0
    return row["total"]


def list_overdue_project_names():
    today = helpers.today_string()
    rows = database.run_query(
        """
        SELECT project_name FROM projects
        WHERE status IN ('Pending', 'Ongoing')
          AND expected_end_date < %s
        ORDER BY expected_end_date
        """,
        (today,),
        fetch="all"
    )
    if rows is None:
        return []
    return [r["project_name"] for r in rows]
