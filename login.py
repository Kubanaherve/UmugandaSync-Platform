# login.py
# Admin login OR community member login (two different roles)

import database
import helpers
import menu
import languages


def choose_entry_type():
    helpers.clear_screen()
    menu.show_login_header()
    print("-" * 44)
    print(languages.t("entry_title"))
    print("-" * 44)
    print(languages.t("entry_admin"))
    print(languages.t("entry_member"))
    print(languages.t("entry_exit"))
    print("-" * 44)
    helpers.tip("Admin manages the whole village system.")
    helpers.tip("Member only views personal Umuganda record.")
    print()
    choice = input(languages.t("entry_prompt")).strip()

    if choice == "1":
        return "admin"
    elif choice == "2":
        return "member"
    elif choice == "0":
        return "exit"
    else:
        helpers.error(languages.t("invalid_choice"))
        return None


def login():
    helpers.clear_screen()
    menu.show_login_header()
    print(languages.t("please_login"))
    print(languages.t("demo_login"))
    print()

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        username = helpers.get_non_empty(languages.t("username"))
        password = helpers.get_non_empty(languages.t("password"))

        sql = """
            SELECT admin_id, username, full_name
            FROM admins
            WHERE username = %s AND password = %s
        """
        row = database.run_query(sql, (username, password), fetch="one")

        if row != None:
            helpers.success(languages.t("login_ok") + " " + row["full_name"] + "!")
            helpers.pause()
            return row

        attempts = attempts + 1
        left = max_attempts - attempts
        helpers.error(languages.t("login_bad"))
        if left > 0:
            print(languages.t("attempts_left"), left)
            print()

    helpers.error(languages.t("too_many_attempts"))
    return None


def member_login():
    helpers.clear_screen()
    helpers.print_line(languages.t("member_entry_title"))
    print(languages.t("member_entry_help"))
    print(languages.t("member_demo"))
    print()

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
        phone = helpers.get_non_empty(languages.t("member_phone_prompt"))

        sql = """
            SELECT *
            FROM members
            WHERE member_id = %s AND phone = %s
        """
        row = database.run_query(sql, (member_id, phone), fetch="one")

        if row != None:
            if row["status"] != "Active":
                helpers.error(languages.t("member_inactive"))
                helpers.pause()
                return None

            helpers.success(
                languages.t("member_login_ok") + " " +
                row["first_name"] + " " + row["last_name"] + "!"
            )
            print("  Village:", row["village"], "| Cell:", row["cell_name"])
            print("  Phone  :", row["phone"], "| ID:", row["member_id"])
            helpers.pause()
            return row

        attempts = attempts + 1
        left = max_attempts - attempts
        helpers.error(languages.t("member_login_bad"))
        if left > 0:
            print(languages.t("attempts_left"), left)
            print()

    helpers.error(languages.t("too_many_attempts"))
    return None


def show_member_menu():
    print()
    print("-" * 44)
    print(languages.t("member_menu_title"))
    print("-" * 44)
    print(languages.t("member_menu_summary"))
    print(languages.t("member_menu_history"))
    print(languages.t("member_menu_language"))
    print(languages.t("member_menu_logout"))
    print(languages.t("member_menu_exit"))
    print("-" * 44)
