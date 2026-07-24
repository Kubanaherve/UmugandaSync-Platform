# members.py
# Owner: Sonia
# member management for UmugandaSync
# uses database.py from Rebecca

import database
import helpers
import languages


def member_menu():
    running = True
    while running:
        helpers.print_line(languages.t("member_menu"))
        print(languages.t("m1"))
        print(languages.t("m2"))
        print(languages.t("m3"))
        print(languages.t("m4"))
        print(languages.t("m5"))
        print(languages.t("m6"))
        print(languages.t("m7"))
        print(languages.t("m0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            add_member()
        elif choice == "2":
            view_members()
        elif choice == "3":
            search_member()
        elif choice == "4":
            update_member()
        elif choice == "5":
            delete_member()
        elif choice == "6":
            set_member_status("Inactive")
        elif choice == "7":
            set_member_status("Active")
        elif choice == "0":
            running = False
        else:
            print(languages.t("invalid_choice"))


def add_member():
    helpers.print_line("ADD MEMBER")

    national_id = input("National ID (optional, Enter to skip): ").strip()
    if national_id == "":
        national_id = None

    first_name = helpers.get_non_empty("First name: ")
    last_name = helpers.get_non_empty("Last name: ")
    phone = helpers.get_non_empty("Phone number: ")

    # check duplicate phone
    check = database.run_query(
        "SELECT member_id FROM members WHERE phone = %s",
        (phone,),
        fetch="one"
    )
    if check != None:
        print("Error: this phone number is already registered.")
        helpers.pause()
        return

    village = helpers.get_non_empty("Village: ")
    cell_name = helpers.get_non_empty("Cell: ")

    print("Gender: 1=Male  2=Female  3=Other")
    g = input("Choose gender: ").strip()
    if g == "1":
        gender = "Male"
    elif g == "2":
        gender = "Female"
    else:
        gender = "Other"

    date_registered = helpers.today_string()

    sql = """
        INSERT INTO members
        (national_id, first_name, last_name, phone, village, cell_name,
         gender, date_registered, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active')
    """
    values = (national_id, first_name, last_name, phone, village, cell_name, gender, date_registered)
    new_id = database.run_query(sql, values)

    if new_id != None:
        print("Member added successfully. Member ID:", new_id)
    else:
        print("Failed to add member.")
    helpers.pause()


def view_members():
    helpers.print_line("ALL MEMBERS")
    rows = database.run_query("SELECT * FROM members ORDER BY member_id", fetch="all")

    if rows == None or len(rows) == 0:
        print("No members found.")
    else:
        for row in rows:
            print(row["member_id"], "|", row["first_name"], row["last_name"], "|",
                  row["phone"], "|", row["village"], "/", row["cell_name"], "|",
                  row["gender"], "|", row["status"])
        print("Total members:", len(rows))
    helpers.pause()


def search_member():
    helpers.print_line("SEARCH MEMBER")
    print("1. By Member ID")
    print("2. By Name")
    print("3. By Phone")
    choice = input("Enter choice: ").strip()

    rows = None
    if choice == "1":
        member_id = helpers.get_positive_int("Member ID: ")
        rows = database.run_query(
            "SELECT * FROM members WHERE member_id = %s",
            (member_id,),
            fetch="all"
        )
    elif choice == "2":
        name = helpers.get_non_empty("Name (first or last): ")
        like_name = "%" + name + "%"
        rows = database.run_query(
            """
            SELECT * FROM members
            WHERE first_name LIKE %s OR last_name LIKE %s
            ORDER BY first_name
            """,
            (like_name, like_name),
            fetch="all"
        )
    elif choice == "3":
        phone = helpers.get_non_empty("Phone: ")
        rows = database.run_query(
            "SELECT * FROM members WHERE phone = %s",
            (phone,),
            fetch="all"
        )
    else:
        print("Invalid choice.")
        helpers.pause()
        return

    if rows == None or len(rows) == 0:
        print("No member found.")
    else:
        for row in rows:
            print("ID:", row["member_id"], "| Name:", row["first_name"], row["last_name"],
                  "| Phone:", row["phone"], "| Village:", row["village"],
                  "| Status:", row["status"])
    helpers.pause()


def update_member():
    helpers.print_line("UPDATE MEMBER")
    member_id = helpers.get_positive_int("Member ID to update: ")
    row = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if row == None:
        print("Member not found.")
        helpers.pause()
        return

    print("Current:", row["first_name"], row["last_name"], row["phone"])
    first_name = helpers.get_non_empty("New first name: ")
    last_name = helpers.get_non_empty("New last name: ")
    phone = helpers.get_non_empty("New phone: ")
    village = helpers.get_non_empty("New village: ")
    cell_name = helpers.get_non_empty("New cell: ")

    dup = database.run_query(
        "SELECT member_id FROM members WHERE phone = %s AND member_id <> %s",
        (phone, member_id),
        fetch="one"
    )
    if dup != None:
        print("Error: phone already used by another member.")
        helpers.pause()
        return

    result = database.run_query(
        """
        UPDATE members
        SET first_name=%s, last_name=%s, phone=%s, village=%s, cell_name=%s
        WHERE member_id=%s
        """,
        (first_name, last_name, phone, village, cell_name, member_id)
    )
    if result != None:
        print("Member updated successfully.")
    else:
        print("Update failed.")
    helpers.pause()


def delete_member():
    helpers.print_line("DELETE MEMBER")
    member_id = helpers.get_positive_int("Member ID to delete: ")
    row = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if row == None:
        print("Member not found.")
        helpers.pause()
        return

    print("You will delete:", row["first_name"], row["last_name"])
    ok = helpers.confirm("Are you sure? This cannot be undone")
    if ok == True:
        result = database.run_query(
            "DELETE FROM members WHERE member_id = %s",
            (member_id,)
        )
        if result != None:
            print("Member deleted.")
        else:
            print("Could not delete. Maybe they have attendance or borrows.")
            print("Tip: deactivate the member instead.")
    else:
        print("Delete cancelled.")
    helpers.pause()


def set_member_status(new_status):
    helpers.print_line("SET MEMBER STATUS: " + new_status)
    member_id = helpers.get_positive_int("Member ID: ")
    row = database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if row == None:
        print("Member not found.")
        helpers.pause()
        return

    result = database.run_query(
        "UPDATE members SET status = %s WHERE member_id = %s",
        (new_status, member_id)
    )
    if result != None:
        print("Member status changed to", new_status)
    else:
        print("Failed to update status.")
    helpers.pause()


def member_exists(member_id):
    # other modules use this (Cynthia, Marvella, Rosette)
    row = database.run_query(
        "SELECT member_id FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if row == None:
        return False
    return True
