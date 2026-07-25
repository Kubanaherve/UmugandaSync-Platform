import logging
from typing import Optional

import database
import helpers
import menu
import languages
import config

logger = logging.getLogger(__name__)

ATTEMPT_STORE: dict[str, int] = {}


def choose_entry_type() -> Optional[str]:
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
        logger.debug("User selected admin entry")
        return "admin"
    elif choice == "2":
        logger.debug("User selected member entry")
        return "member"
    elif choice == "0":
        logger.debug("User selected exit")
        return "exit"
    else:
        helpers.error(languages.t("invalid_choice"))
        return None


def login() -> Optional[dict]:
    helpers.clear_screen()
    menu.show_login_header()
    print(languages.t("please_login"))
    print(languages.t("demo_login"))
    print()

    remaining = config.MAX_LOGIN_ATTEMPTS

    while remaining > 0:
        username = helpers.get_non_empty(languages.t("username"))
        password = helpers.get_non_empty(languages.t("password"))

        row = database.run_query(
            """SELECT admin_id, username, full_name
               FROM admins
               WHERE username = %s AND password = %s""",
            (username, password),
            fetch="one",
        )

        if row is not None:
            ATTEMPT_STORE["admin"] = 0
            logger.info(f"Admin '{row['full_name']}' logged in successfully")
            helpers.success(languages.t("login_ok") + " " + row["full_name"] + "!")
            helpers.pause()
            return row

        remaining -= 1
        ATTEMPT_STORE["admin"] = ATTEMPT_STORE.get("admin", 0) + 1
        helpers.error(languages.t("login_bad"))
        if remaining > 0:
            print(languages.t("attempts_left"), remaining)
            print()

    logger.warning(f"Admin login failed after {config.MAX_LOGIN_ATTEMPTS} attempts")
    helpers.error(languages.t("too_many_attempts"))
    return None


def member_login() -> Optional[dict]:
    helpers.clear_screen()
    helpers.print_line(languages.t("member_entry_title"))
    print(languages.t("member_entry_help"))
    print(languages.t("member_demo"))
    print()

    remaining = config.MAX_LOGIN_ATTEMPTS
    member_key = "member"

    while remaining > 0:
        member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
        phone = helpers.get_non_empty(languages.t("member_phone_prompt"))

        row = database.run_query(
            """SELECT *
               FROM members
               WHERE member_id = %s AND phone = %s""",
            (member_id, phone),
            fetch="one",
        )

        if row is not None:
            if row["status"] != "Active":
                helpers.error(languages.t("member_inactive"))
                logger.warning(
                    f"Inactive member ID {member_id} attempted login"
                )
                helpers.pause()
                return None

            ATTEMPT_STORE[member_key] = 0
            full_name = f"{row['first_name']} {row['last_name']}"
            logger.info(f"Member '{full_name}' (ID {member_id}) logged in")
            helpers.success(
                languages.t("member_login_ok") + " " + full_name + "!"
            )
            print(f"  Village: {row['village']} | Cell: {row['cell_name']}")
            print(f"  Phone  : {row['phone']} | ID: {row['member_id']}")
            helpers.pause()
            return row

        remaining -= 1
        ATTEMPT_STORE[member_key] = ATTEMPT_STORE.get(member_key, 0) + 1
        helpers.error(languages.t("member_login_bad"))
        if remaining > 0:
            print(languages.t("attempts_left"), remaining)
            print()

    logger.warning(f"Member login failed after {config.MAX_LOGIN_ATTEMPTS} attempts")
    helpers.error(languages.t("too_many_attempts"))
    return None


def show_member_menu() -> None:
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
