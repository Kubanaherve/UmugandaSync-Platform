import logging
import sys
from dataclasses import dataclass, field
from typing import Optional

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
import csv_export
import reports
import helpers
import languages
import config

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


@dataclass
class AppSession:
    admin: Optional[dict] = None
    member: Optional[dict] = None
    running: bool = True

    @property
    def is_admin(self) -> bool:
        return self.admin is not None

    @property
    def is_member(self) -> bool:
        return self.member is not None

    @property
    def display_name(self) -> str:
        if self.admin:
            return self.admin.get("full_name", "Admin")
        if self.member:
            return f"{self.member.get('first_name', '')} {self.member.get('last_name', '')}"
        return "User"

    def end(self) -> None:
        self.running = False

    def clear(self) -> None:
        self.admin = None
        self.member = None


def check_database_ready() -> bool:
    logger.info("Checking database connection...")
    print(languages.t("connecting"))
    ok = database.test_connection()
    if not ok:
        print()
        print(languages.t("setup_help"))
        for i in range(1, 4):
            print(languages.t(f"setup{i}"))
        print()
        helpers.tip("Or run: python3 setup_database.py")
        logger.warning("Database connection failed")
        return False
    logger.info("Database connection successful")
    return True


def show_home(admin_name: str) -> None:
    helpers.clear_screen()
    dashboard.show_dashboard(admin_name)
    notifications.show_notifications()


def run_admin_session(session: AppSession) -> str:
    session.admin = login.login()
    if session.admin is None:
        return "back"

    show_home(session.admin["full_name"])

    while session.running:
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
            print()
            print("  a. " + languages.t("menu_reports_sub"))
            print("  b. " + languages.t("menu_csv_export"))
            sub = input("  (a/b): ").strip().lower()
            if sub == "b":
                csv_export.show_csv_export_menu()
            else:
                reports.reports_menu()
        elif choice == "6":
            search.search_menu()
        elif choice == "7":
            print(languages.t("refreshing"))
            show_home(session.admin["full_name"])
        elif choice == "8":
            languages.choose_language()
            helpers.pause()
        elif choice == "9":
            helpers.success(languages.t("logged_out"))
            logger.info(f"Admin '{session.display_name}' logged out")
            session.clear()
            return "back"
        elif choice == "0":
            print(languages.t("goodbye"))
            session.end()
            return "exit"
        else:
            helpers.error(languages.t("invalid_choice"))
            helpers.pause()

    return "exit"


def run_member_session(session: AppSession) -> str:
    session.member = login.member_login()
    if session.member is None:
        return "back"

    helpers.clear_screen()
    attendance.member_lifetime_summary(session.member)

    while session.running:
        login.show_member_menu()
        choice = menu.get_choice()

        if choice == "1":
            helpers.clear_screen()
            attendance.member_lifetime_summary(session.member)
        elif choice == "2":
            helpers.clear_screen()
            attendance.member_own_history(session.member)
        elif choice == "3":
            languages.choose_language()
            helpers.pause()
        elif choice == "4":
            helpers.success(languages.t("logged_out"))
            logger.info(f"Member '{session.display_name}' logged out")
            session.clear()
            return "back"
        elif choice == "0":
            print(languages.t("goodbye"))
            session.end()
            return "exit"
        else:
            helpers.error(languages.t("invalid_choice"))
            helpers.pause()

    return "exit"


def main() -> None:
    _setup_logging()
    logger.info(f"{config.APP_NAME} v{config.APP_VERSION} starting")

    helpers.clear_screen()
    languages.choose_language()

    if not check_database_ready():
        return

    session = AppSession()

    while session.running:
        entry = login.choose_entry_type()

        if entry is None:
            helpers.pause()
        elif entry == "exit":
            print(languages.t("goodbye"))
            logger.info("Application exited by user")
            session.end()
        elif entry == "admin":
            result = run_admin_session(session)
            if result == "exit":
                session.end()
        elif entry == "member":
            result = run_member_session(session)
            if result == "exit":
                session.end()

    logger.info(f"{config.APP_NAME} v{config.APP_VERSION} shutting down")


if __name__ == "__main__":
    main()
