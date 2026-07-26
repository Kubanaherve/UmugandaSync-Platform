# tools.py
# Owner: Rosette
# Inventory and borrow/return tools.
# Reusable helpers (get_tool_by_id, ask_condition_status, format_tool_line,
# adjust_available_quantity) keep the CRUD/borrow/return actions short and
# avoid repeating the same query or menu logic in multiple places.

import database
import helpers
import members
import languages


CONDITION_MAP = {
    "1": "Good",
    "2": "Needs Repair",
    "3": "Broken",
}


def ask_condition_status(default=None):
    """Ask the user to pick a condition status. Falls back to default (or 'Good')."""
    print("Condition: 1=Good  2=Needs Repair  3=Broken")
    cond_choice = input("Choose condition: ").strip()
    return CONDITION_MAP.get(cond_choice, default if default else "Good")


def adjust_available_quantity(tool_id, new_available):
    """Persist a new available_quantity value for a tool."""
    return database.run_query(
        "UPDATE tools SET available_quantity = %s WHERE tool_id = %s",
        (new_available, tool_id)
    )


def format_tool_line(row):
    """Build a single display line for a tool row, flagging low stock."""
    flag = " << LOW STOCK" if row["available_quantity"] <= row["low_stock_limit"] else ""
    return (
        f'ID: {row["tool_id"]} | {row["tool_name"]} | {row["category"]} | '
        f'Available: {row["available_quantity"]}/{row["total_quantity"]} | '
        f'{row["condition_status"]}{flag}'
    )


def get_tool_by_id(tool_id):
    """Fetch a single tool row by its ID, or None if it does not exist."""
    return database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )


def tools_menu():
    """Show the tools menu loop and dispatch user choices to the right action."""
    running = True
    while running:
        helpers.print_line(languages.t("tools_menu"))
        print(languages.t("t1"))
        print(languages.t("t2"))
        print(languages.t("t3"))
        print(languages.t("t4"))
        print(languages.t("t5"))
        print(languages.t("t6"))
        print(languages.t("t7"))
        print(languages.t("t8"))
        print(languages.t("t0"))
        choice = input(languages.t("enter_choice")).strip()

        actions = {
            "1": add_tool,
            "2": view_tools,
            "3": update_tool,
            "4": delete_tool,
            "5": borrow_tool,
            "6": return_tool,
            "7": lambda: low_stock_warning(show_pause=True),
            "8": view_borrow_history,
        }

        if choice == "0":
            running = False
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice.")


def add_tool():
    """Register a brand new tool in the inventory."""
    helpers.print_line("REGISTER TOOL")
    tool_name = helpers.get_non_empty("Tool name: ")
    category = helpers.get_non_empty("Category: ")
    total_quantity = helpers.get_positive_int("Total quantity: ")
    if total_quantity <= 0:
        print("Quantity must be greater than 0.")
        helpers.pause()
        return

    available_quantity = total_quantity
    condition_status = ask_condition_status()
    low_stock_limit = helpers.get_positive_int("Low stock limit: ")

    if low_stock_limit > total_quantity:
        print("Warning: low stock limit is higher than total quantity.")

    result = database.run_query(
        """
        INSERT INTO tools
        (tool_name, category, total_quantity, available_quantity,
         condition_status, low_stock_limit)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            tool_name, category, total_quantity, available_quantity,
            condition_status, low_stock_limit
        )
    )
    if result is not None:
        print("Tool registered. ID:", result)
    else:
        print("Failed to register tool.")
    helpers.pause()


def view_tools():
    """List every tool in the inventory, flagging any that are low on stock."""
    helpers.print_line("ALL TOOLS")
    rows = database.run_query(
        "SELECT * FROM tools ORDER BY tool_id",
        fetch="all"
    )
    if not rows:
        print("No tools found.")
    else:
        for row in rows:
            print(format_tool_line(row))
    helpers.pause()


def update_tool():
    """Edit an existing tool's details, with basic consistency checks."""
    helpers.print_line("UPDATE TOOL")
    tool_id = helpers.get_positive_int("Tool ID: ")
    row = get_tool_by_id(tool_id)
    if row is None:
        print("Tool not found.")
        helpers.pause()
        return

    print("Current:", row["tool_name"],
          "available", row["available_quantity"], "/", row["total_quantity"])

    tool_name = helpers.get_non_empty("Tool name: ")
    category = helpers.get_non_empty("Category: ")
    total_quantity = helpers.get_positive_int("Total quantity: ")
    available_quantity = helpers.get_positive_int("Available quantity: ")

    if available_quantity > total_quantity:
        print("Error: available cannot be greater than total.")
        helpers.pause()
        return

    condition_status = ask_condition_status(default=row["condition_status"])
    low_stock_limit = helpers.get_positive_int("Low stock limit: ")

    result = database.run_query(
        """
        UPDATE tools
        SET tool_name=%s, category=%s, total_quantity=%s,
            available_quantity=%s, condition_status=%s, low_stock_limit=%s
        WHERE tool_id=%s
        """,
        (
            tool_name, category, total_quantity, available_quantity,
            condition_status, low_stock_limit, tool_id
        )
    )
    if result is not None:
        print("Tool updated.")
    else:
        print("Update failed.")
    helpers.pause()


def delete_tool():
    """Remove a tool from the inventory after confirmation."""
    helpers.print_line("DELETE TOOL")
    tool_id = helpers.get_positive_int("Tool ID: ")
    row = get_tool_by_id(tool_id)
    if row is None:
        print("Tool not found.")
        helpers.pause()
        return

    print("Delete tool:", row["tool_name"])
    if helpers.confirm("Are you sure") is True:
        result = database.run_query(
            "DELETE FROM tools WHERE tool_id = %s",
            (tool_id,)
        )
        if result is not None:
            print("Tool deleted.")
        else:
            print("Could not delete. There may be borrow history linked.")
    else:
        print("Cancelled.")
    helpers.pause()


def borrow_tool():
    """Borrow a tool for a member, reducing the available stock."""
    helpers.print_line("BORROW TOOL")
    tool_id = helpers.get_positive_int("Tool ID: ")
    tool = get_tool_by_id(tool_id)
    if tool is None:
        print("Tool not found.")
        helpers.pause()
        return

    if tool["condition_status"] == "Broken":
        print("This tool cannot be borrowed (Broken).")
        helpers.pause()
        return

    if tool["available_quantity"] <= 0:
        print("No available stock for this tool.")
        helpers.pause()
        return

    member_id = helpers.get_required_national_id("National ID borrowing: ")
    if not members.member_exists(member_id):
        print("Member not found.")
        helpers.pause()
        return

    quantity = helpers.get_positive_int("Quantity to borrow: ")
    if quantity <= 0:
        print("Quantity must be greater than 0.")
        helpers.pause()
        return

    if quantity > tool["available_quantity"]:
        print("Not enough stock. Available:", tool["available_quantity"])
        helpers.pause()
        return

    borrow_date = helpers.today_string()
    new_available = tool["available_quantity"] - quantity

    with database.transaction() as cursor:
        if cursor is None:
            print("Database error. Could not connect.")
            helpers.pause()
            return
        cursor.execute(
            """
            INSERT INTO tool_borrows
            (tool_id, member_id, quantity, borrow_date, return_date, status)
            VALUES (%s, %s, %s, %s, NULL, 'Borrowed')
            """,
            (tool_id, member_id, quantity, borrow_date)
        )
        cursor.execute(
            "UPDATE tools SET available_quantity = %s WHERE tool_id = %s",
            (new_available, tool_id)
        )

    print("Borrowed successfully. Remaining available:", new_available)

    if new_available <= tool["low_stock_limit"]:
        print("WARNING: stock is now low for", tool["tool_name"])

    helpers.pause()


def return_tool():
    """Mark a borrow record as returned and restore stock (capped at total)."""
    helpers.print_line("RETURN TOOL")
    borrow_id = helpers.get_positive_int("Borrow ID to return: ")
    borrow = database.run_query(
        """
        SELECT b.*, t.tool_name, t.available_quantity, t.total_quantity
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        WHERE b.borrow_id = %s
        """,
        (borrow_id,),
        fetch="one"
    )
    if borrow is None:
        print("Borrow record not found.")
        helpers.pause()
        return

    if borrow["status"] != "Borrowed":
        print("This borrow is already returned.")
        helpers.pause()
        return

    return_date = helpers.today_string()
    new_available = min(
        borrow["available_quantity"] + borrow["quantity"],
        borrow["total_quantity"]
    )

    with database.transaction() as cursor:
        if cursor is None:
            print("Database error. Could not connect.")
            helpers.pause()
            return
        cursor.execute(
            """
            UPDATE tool_borrows
            SET status='Returned', return_date=%s
            WHERE borrow_id=%s
            """,
            (return_date, borrow_id)
        )
        cursor.execute(
            "UPDATE tools SET available_quantity = %s WHERE tool_id = %s",
            (new_available, borrow["tool_id"])
        )

    print("Returned:", borrow["tool_name"], "x", borrow["quantity"])
    print("Available now:", new_available)
    helpers.pause()


def low_stock_warning(show_pause=False):
    """Print (and return) all tools whose available quantity is at/below limit."""
    helpers.print_line("LOW STOCK WARNING")
    rows = database.run_query(
        """
        SELECT * FROM tools
        WHERE available_quantity <= low_stock_limit
        ORDER BY available_quantity
        """,
        fetch="all"
    )
    if not rows:
        print("No low stock tools. Good job!")
    else:
        print("WARNING:", len(rows), "tool(s) are low on stock:")
        for row in rows:
            print(
                "-", row["tool_name"],
                "available:", row["available_quantity"],
                "(limit:", str(row["low_stock_limit"]) + ")"
            )
    if show_pause:
        helpers.pause()
    return rows


def view_borrow_history():
    """Show every borrow record, most recent first, with member and tool info."""
    helpers.print_line("BORROW HISTORY")
    rows = database.run_query(
        """
        SELECT b.borrow_id, b.quantity, b.borrow_date, b.return_date, b.status,
               t.tool_name, m.first_name, m.last_name
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        JOIN members m ON b.member_id = m.national_id
        ORDER BY b.borrow_id DESC
        """,
        fetch="all"
    )
    if rows is None or len(rows) == 0:
        print("No borrow history.")
    else:
        for row in rows:
            print(
                "Borrow#", row["borrow_id"], "|",
                row["tool_name"], "x", row["quantity"], "|",
                row["first_name"], row["last_name"], "|",
                row["borrow_date"], "->", row["return_date"], "|",
                row["status"]
            )
    helpers.pause()


def count_low_stock_tools():
    """Return the number of tools currently at/below their low stock limit."""
    row = database.run_query(
        """
        SELECT COUNT(*) AS total FROM tools
        WHERE available_quantity <= low_stock_limit
        """,
        fetch="one"
    )
    if row is None:
        return 0
    return row["total"]
