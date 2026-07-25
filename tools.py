# tools.py
# Tool inventory management for UmugandaSync

from datetime import datetime
import database
import helpers
import languages


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
            register_tool()
        elif choice == "2":
            view_all_tools()
        elif choice == "3":
            update_tool()
        elif choice == "4":
            delete_tool()
        elif choice == "5":
            borrow_tool()
        elif choice == "6":
            return_tool()
        elif choice == "7":
            low_stock_warning()
        elif choice == "8":
            view_borrow_history()
        elif choice == "0":
            running = False
        else:
            helpers.error(languages.t("invalid_choice"))


def register_tool():
    helpers.print_line(languages.t("t1"))
    tool_name = helpers.get_non_empty(languages.t("tool_name_prompt"))
    category = helpers.get_non_empty(languages.t("tool_category_prompt"))
    total_qty = helpers.get_positive_int(languages.t("tool_total_qty_prompt"))
    available_qty = helpers.get_positive_int(languages.t("tool_avail_qty_prompt"))
    condition = helpers.get_non_empty(languages.t("tool_condition_prompt"))
    low_stock = helpers.get_positive_int(languages.t("tool_low_stock_prompt"))

    sql = """
        INSERT INTO tools
        (tool_name, category, total_quantity, available_quantity, condition_status, low_stock_limit)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    result = database.run_query(sql, (tool_name, category, total_qty, available_qty, condition, low_stock))
    if result is not None:
        helpers.success(languages.t("tool_added") + " (ID: " + str(result) + ")")
    else:
        helpers.error(languages.t("tool_add_failed"))
    helpers.pause()


def view_all_tools():
    helpers.print_line(languages.t("t2"))
    rows = database.run_query(
        "SELECT * FROM tools ORDER BY tool_name",
        fetch="all"
    )
    if not rows:
        print(languages.t("no_tools"))
    else:
        for row in rows:
            low = ""
            if row["available_quantity"] <= row["low_stock_limit"]:
                low = " LOW STOCK"
            print(
                str(row["tool_id"]).ljust(4),
                row["tool_name"].ljust(20),
                "Cat:", row["category"].ljust(12),
                "Avail:", str(row["available_quantity"]).rjust(3),
                "/", str(row["total_quantity"]).rjust(3),
                "Cond:", row["condition_status"].ljust(14),
                low
            )
    helpers.pause()


def update_tool():
    helpers.print_line(languages.t("t3"))
    tool_id = helpers.get_positive_int(languages.t("tool_id_prompt"))
    row = database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )
    if row is None:
        helpers.error(languages.t("tool_not_found"))
        helpers.pause()
        return

    print(languages.t("current_values") + ":")
    print("  ", row["tool_name"], "|", row["category"], "|",
          str(row["total_quantity"]), "/", str(row["available_quantity"]), "|",
          row["condition_status"])

    tool_name = helpers.get_non_empty(languages.t("tool_name_prompt") + " [" + row["tool_name"] + "]: ")
    category = helpers.get_non_empty(languages.t("tool_category_prompt") + " [" + row["category"] + "]: ")
    total_qty = helpers.get_positive_int(languages.t("tool_total_qty_prompt") + " [" + str(row["total_quantity"]) + "]: ")
    avail_qty = helpers.get_positive_int(languages.t("tool_avail_qty_prompt") + " [" + str(row["available_quantity"]) + "]: ")
    condition = helpers.get_non_empty(languages.t("tool_condition_prompt") + " [" + row["condition_status"] + "]: ")

    sql = """
        UPDATE tools
        SET tool_name=%s, category=%s, total_quantity=%s,
            available_quantity=%s, condition_status=%s
        WHERE tool_id=%s
    """
    result = database.run_query(sql, (tool_name, category, total_qty, avail_qty, condition, tool_id))
    if result is not None:
        helpers.success(languages.t("tool_updated"))
    else:
        helpers.error(languages.t("tool_update_failed"))
    helpers.pause()


def delete_tool():
    helpers.print_line(languages.t("t4"))
    tool_id = helpers.get_positive_int(languages.t("tool_id_prompt"))
    row = database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )
    if row is None:
        helpers.error(languages.t("tool_not_found"))
        helpers.pause()
        return

    print(languages.t("confirm_delete") + ":", row["tool_name"])
    ok = helpers.confirm(languages.t("are_you_sure"))
    if ok:
        result = database.run_query("DELETE FROM tools WHERE tool_id = %s", (tool_id,))
        if result is not None:
            helpers.success(languages.t("tool_deleted"))
        else:
            helpers.error(languages.t("tool_delete_failed"))
    helpers.pause()


def borrow_tool():
    helpers.print_line(languages.t("t5"))
    tool_id = helpers.get_positive_int(languages.t("tool_id_prompt"))
    tool = database.run_query(
        "SELECT * FROM tools WHERE tool_id = %s",
        (tool_id,),
        fetch="one"
    )
    if tool is None:
        helpers.error(languages.t("tool_not_found"))
        helpers.pause()
        return

    print(languages.t("tool_selected") + ":", tool["tool_name"],
          "|", languages.t("tool_available") + ":", tool["available_quantity"])

    member_id = helpers.get_positive_int(languages.t("member_id_prompt"))
    member_check = database.run_query(
        "SELECT member_id FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one"
    )
    if member_check is None:
        helpers.error(languages.t("member_not_found"))
        helpers.pause()
        return

    quantity = helpers.get_positive_int(languages.t("tool_quantity_prompt"))
    if quantity > tool["available_quantity"]:
        helpers.error(languages.t("tool_not_enough"))
        helpers.pause()
        return

    today = helpers.today_string()
    sql_borrow = """
        INSERT INTO tool_borrows (tool_id, member_id, quantity, borrow_date, status)
        VALUES (%s, %s, %s, %s, 'Borrowed')
    """
    sql_update = """
        UPDATE tools SET available_quantity = available_quantity - %s
        WHERE tool_id = %s
    """
    result_borrow = database.run_query(sql_borrow, (tool_id, member_id, quantity, today))
    if result_borrow is not None:
        database.run_query(sql_update, (quantity, tool_id))
        helpers.success(languages.t("tool_borrowed"))
    else:
        helpers.error(languages.t("tool_borrow_failed"))
    helpers.pause()


def return_tool():
    helpers.print_line(languages.t("t6"))
    borrow_id = helpers.get_positive_int(languages.t("borrow_id_prompt"))
    borrow = database.run_query(
        """
        SELECT b.*, t.tool_name
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        WHERE b.borrow_id = %s AND b.status = 'Borrowed'
        """,
        (borrow_id,),
        fetch="one"
    )
    if borrow is None:
        helpers.error(languages.t("borrow_not_found"))
        helpers.pause()
        return

    print(languages.t("borrow_info") + ":", borrow["tool_name"],
          "x" + str(borrow["quantity"]), "|", languages.t("borrowed_by"),
          borrow["member_id"], "|", languages.t("since"), borrow["borrow_date"])

    ok = helpers.confirm(languages.t("confirm_return"))
    if ok:
        today = helpers.today_string()
        database.run_query(
            "UPDATE tool_borrows SET return_date=%s, status='Returned' WHERE borrow_id=%s",
            (today, borrow_id)
        )
        database.run_query(
            "UPDATE tools SET available_quantity = available_quantity + %s WHERE tool_id=%s",
            (borrow["quantity"], borrow["tool_id"])
        )
        helpers.success(languages.t("tool_returned"))
    helpers.pause()


def low_stock_warning():
    helpers.print_line(languages.t("t7"))
    rows = database.run_query(
        """
        SELECT tool_name, available_quantity, low_stock_limit, category
        FROM tools
        WHERE available_quantity <= low_stock_limit
        ORDER BY available_quantity
        """,
        fetch="all"
    )
    count = count_low_stock_tools()
    if count == 0:
        print(languages.t("no_low_stock"))
    else:
        print(languages.t("tools_low_stock_count") + ":", count)
        print()
        for row in rows:
            print("  -", row["tool_name"],
                  "(" + row["category"] + "):",
                  str(row["available_quantity"]), "/", str(row["low_stock_limit"]),
                  "remaining")
    helpers.pause()


def view_borrow_history():
    helpers.print_line(languages.t("t8"))
    rows = database.run_query(
        """
        SELECT b.borrow_id, t.tool_name, m.first_name, m.last_name,
               b.quantity, b.borrow_date, b.return_date, b.status
        FROM tool_borrows b
        JOIN tools t ON b.tool_id = t.tool_id
        JOIN members m ON b.member_id = m.member_id
        ORDER BY b.borrow_date DESC
        """,
        fetch="all"
    )
    if not rows:
        print(languages.t("no_borrows"))
    else:
        for row in rows:
            returned = row["return_date"] if row["return_date"] else languages.t("not_returned")
            print(
                "B#" + str(row["borrow_id"]),
                row["tool_name"], "x" + str(row["quantity"]),
                "->", row["first_name"], row["last_name"],
                "|", languages.t("borrowed"), row["borrow_date"],
                "|", languages.t("returned"), returned,
                "|", row["status"]
            )
    helpers.pause()


def count_low_stock_tools():
    row = database.run_query(
        "SELECT COUNT(*) AS total FROM tools WHERE available_quantity <= low_stock_limit",
        fetch="one"
    )
    if row is None:
        return 0
    return row["total"]
