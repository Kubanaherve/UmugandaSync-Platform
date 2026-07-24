# main.py
# starts UmugandaSync and connects all modules

import database
import menu
import login
import dashboard
import notifications
import search
import members
import attendance
import projects
import tools
import reports
import helpers
import languages


def check_database_ready():
    print(languages.t("connecting"))
    ok = database.test_connection()
    if ok == False:
        print()
        print(languages.t("setup_help"))
        print(languages.t("setup1"))
        print(languages.t("setup2"))
        print(languages.t("setup3"))
        print()
        helpers.tip("Or run: python3 setup_database.py")
        return False
    return True


def show_home(admin_name):
    # clean home screen for village leader
    helpers.clear_screen()
    dashboard.show_dashboard(admin_name)
    notifications.show_notifications()


def run_admin_session():
    admin = login.login()
    if admin == None:
        return "back"

    show_home(admin["full_name"])

    logged_in = True
    while logged_in == True:
        menu.show_main_menu()
        choice = menu.get_choice()

        if choice == "1":
            members.member_menu()
        elif choice == "2":
            attendance.attendance_menu()
        elif choice == "3":
            projects.project_menu()
        elif choice == "4":
            tools.tools_menu()
        elif choice == "5":
            reports.reports_menu()
        elif choice == "6":
            search.search_menu()
        elif choice == "7":
            print(languages.t("refreshing"))
            show_home(admin["full_name"])
        elif choice == "8":
            languages.choose_language()
            helpers.pause()
        elif choice == "9":
            helpers.success(languages.t("logged_out"))
            logged_in = False
        elif choice == "0":
            print(languages.t("goodbye"))
            return "exit"
        else:
            helpers.error(languages.t("invalid_choice"))
            helpers.pause()

    return "back"


def run_member_session():
    member = login.member_login()
    if member == None:
        return "back"

    # show personal summary once at login (friendly journey)
    helpers.clear_screen()
    attendance.member_lifetime_summary(member)

    logged_in = True
    while logged_in == True:
        login.show_member_menu()
        choice = menu.get_choice()

        if choice == "1":
            helpers.clear_screen()
            attendance.member_lifetime_summary(member)
        elif choice == "2":
            helpers.clear_screen()
            attendance.member_own_history(member)
        elif choice == "3":
            languages.choose_language()
            helpers.pause()
        elif choice == "4":
            helpers.success(languages.t("logged_out"))
            logged_in = False
        elif choice == "0":
            print(languages.t("goodbye"))
            return "exit"
        else:
            helpers.error(languages.t("invalid_choice"))
            helpers.pause()

    return "back"


def main():
    helpers.clear_screen()
    languages.choose_language()

    ready = check_database_ready()
    if ready == False:
        return

    running = True
    while running == True:
        entry = login.choose_entry_type()

        if entry == None:
            helpers.pause()
        elif entry == "exit":
            print(languages.t("goodbye"))
            running = False
        elif entry == "admin":
            result = run_admin_session()
            if result == "exit":
                running = False
        elif entry == "member":
            result = run_member_session()
            if result == "exit":
                running = False


if __name__ == "__main__":
    main()
