# tools.py
# Owner: Rosette
# inventory and borrow/return tools

import database
import helpers
import members
import languages


def get_tool_by_id(tool_id):
    """Fetch a single tool row by its ID, or None if it does not exist."""
    return database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )


def tools_menu():
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

        if choice == "1":
            add_tool()
        elif choice == "2":
            view_tools()
        elif choice == "3":
            update_tool()
        elif choice == "4":
            delete_tool()
        elif choice == "5":
            borrow_tool()
        elif choice == "6":
            return_tool()
        elif choice == "7":
            low_stock_warning(show_pause=True)
        elif choice == "8":
            view_borrow_history()
        elif choice == "0":
            running = False
        else:
            print("Invalid choice.")


def add_tool():
    # add new tool to inventory
    helpers.print_line("REGISTER TOOL")
    tool_name = helpers.get_non_empty("Tool name: ")
    category = helpers.get_non_empty("Category: ")
    total_quantity = helpers.get_positive_int("Total quantity: ")
    if total_quantity <= 0:
        print("Quantity must be greater than 0.")
        helpers.pause()
        return

    available_quantity = total_quantity

    print("Condition: 1=Good  2=Needs Repair  3=Broken  4=Lost")
    cond_choice = input("Choose condition: ").strip()
    if cond_choice == "1":
        condition_status = "Good"
    elif cond_choice == "2":
        condition_status = "Needs Repair"
    elif cond_choice == "3":
        condition_status = "Broken"
    elif cond_choice == "4":
        condition_status = "Lost"
    else:
        condition_status = "Good"

    low_stock_limit = helpers.get_positive_int("Low stock limit: ")

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
    # show all tools
    helpers.print_line("ALL TOOLS")
    rows = database.run_query(
        "SELECT * FROM tools ORDER BY tool_id",
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No tools found.")
    else:
        for row in rows:
            flag = ""
            if row["available_quantity"] <= row["low_stock_limit"]:
                flag = " << LOW STOCK"
            print(
                "ID:", row["tool_id"], "|",
                row["tool_name"], "|",
                row["category"], "|",
                "Available:", row["available_quantity"], "/",
                row["total_quantity"], "|",
                row["condition_status"],
                flag
            )
    helpers.pause()


def update_tool():
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

    print("Condition: 1=Good  2=Needs Repair  3=Broken  4=Lost")
    cond_choice = input("Choose condition: ").strip()
    if cond_choice == "1":
        condition_status = "Good"
    elif cond_choice == "2":
        condition_status = "Needs Repair"
    elif cond_choice == "3":
        condition_status = "Broken"
    elif cond_choice == "4":
        condition_status = "Lost"
    else:
        condition_status = row["condition_status"]

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
    if result != None:
        print("Tool updated.")
    else:
        print("Update failed.")
    helpers.pause()


def delete_tool():
    # delete tool
    helpers.print_line("DELETE TOOL")
    tool_id = helpers.get_positive_int("Tool ID: ")
    row = get_tool_by_id(tool_id)
    if row == None:
        print("Tool not found.")
        helpers.pause()
        return

    print("Delete tool:", row["tool_name"])
    if helpers.confirm("Are you sure") == True:
        result = database.run_query(
            "DELETE FROM tools WHERE tool_id = %s",
            (tool_id,)
        )
        if result != None:
            print("Tool deleted.")
        else:
            print("Could not delete. There may be borrow history linked.")
    else:
        print("Cancelled.")
    helpers.pause()


def borrow_tool():
    # borrow and reduce stock
    helpers.print_line("BORROW TOOL")
    tool_id = helpers.get_positive_int("Tool ID: ")
    tool = database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )
    if tool == None:
        print("Tool not found.")
        helpers.pause()
        return

    if tool["condition_status"] == "Broken" or tool["condition_status"] == "Lost":
        print("This tool cannot be borrowed (Broken/Lost).")
        helpers.pause()
        return

    if tool["available_quantity"] <= 0:
        print("No available stock for this tool.")
        helpers.pause()
        return

    member_id = helpers.get_positive_int("Member ID borrowing: ")
    if members.member_exists(member_id) == False:
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

    borrow_id = database.run_query(
        """
        INSERT INTO tool_borrows
        (tool_id, member_id, quantity, borrow_date, return_date, status)
        VALUES (%s, %s, %s, %s, NULL, 'Borrowed')
        """,
        (tool_id, member_id, quantity, borrow_date)
    )
    if borrow_id == None:
        print("Failed to create borrow record.")
        helpers.pause()
        return

    new_available = tool["available_quantity"] - quantity
    database.run_query(
        "UPDATE tools SET available_quantity = %s WHERE tool_id = %s",
        (new_available, tool_id)
    )
    print("Borrowed successfully. Remaining available:", new_available)

    if new_available <= tool["low_stock_limit"]:
        print("WARNING: stock is now low for", tool["tool_name"])

    helpers.pause()


def return_tool():
    # return borrowed tool
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
    if borrow == None:
        print("Borrow record not found.")
        helpers.pause()
        return

    if borrow["status"] != "Borrowed":
        print("This borrow is already returned.")
        helpers.pause()
        return

    return_date = helpers.today_string()
    database.run_query(
        """
        UPDATE tool_borrows
        SET status='Returned', return_date=%s
        WHERE borrow_id=%s
        """,
        (return_date, borrow_id)
    )

    new_available = borrow["available_quantity"] + borrow["quantity"]
    if new_available > borrow["total_quantity"]:
        new_available = borrow["total_quantity"]

    database.run_query(
        "UPDATE tools SET available_quantity = %s WHERE tool_id = %s",
        (new_available, borrow["tool_id"])
    )
    print("Returned:", borrow["tool_name"], "x", borrow["quantity"])
    print("Available now:", new_available)
    helpers.pause()


def low_stock_warning(show_pause=False):
    # warn about low stock
    helpers.print_line("LOW STOCK WARNING")
    rows = database.run_query(
        """
        SELECT * FROM tools
        WHERE available_quantity <= low_stock_limit
        ORDER BY available_quantity
        """,
        fetch="all"
    )
    if rows == None or len(rows) == 0:
        print("No low stock tools. Good job!")
    else:
        print("WARNING:", len(rows), "tool(s) are low on stock:")
        for row in rows:
            print(
                "-", row["tool_name"],
                "available:", row["available_quantity"],
                "(limit:", str(row["low_stock_limit"]) + ")"
            )
    if show_pause == True:
        helpers.pause()
    return rows


def view_borrow_history():
    helpers.print_line("BORROW HISTORY")
    rows = database.run_query(
        """
        SELECT b.borrow_id, b.quantity, b.borrow_date, b.return_date, b.status,
               t.tool_name, m.first_name, m.last_name
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        JOIN members m ON b.member_id = m.member_id
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
    # count for dashboard
    row = database.run_query(
        """
        SELECT COUNT(*) AS total FROM tools
        WHERE available_quantity <= low_stock_limit
        """,
        fetch="one"
    )
    if row == None:
        return 0
    return row["total"]
