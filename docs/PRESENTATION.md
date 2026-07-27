# UmugandaSync — Presentation Division
# Each person presents ONLY what they built

Total time: about 10–12 minutes
Order: Friend → Rebecca → Sonia → Cynthia → Joshua → Marvella → Rosette → Friend close

Rule: speak about YOUR files only. If asked about another module, say
"That part was built by ___ — they can explain it."

------------------------------------------------------------
1. FRIEND (Project Lead) — 2 minutes
------------------------------------------------------------
Files you made:
  main.py
  menu.py
  login.py
  config.py
  helpers.py
  languages.py
  dashboard.py
  notifications.py
  search.py

What to say:
  "I am the project lead. I built the entry of the system and connected
   everyone's modules.

   First the user chooses language: English, French, or Kinyarwanda.
   Then they choose WHO is entering:
   1 = Village Leader / Admin
   2 = Community Member

   Admin uses username and password.
   Member enters differently with Member ID and phone.

   After admin login, my dashboard shows live totals from MySQL:
   members, today's attendance, ongoing projects, low stock, overdue projects.
   Notifications warn the leader about problems.

   main.py does not contain member or tool logic.
   It only calls Sonia, Cynthia, Joshua, Marvella, and Rosette modules."

Demo (you do first):
  1. Run: python3 main.py
  2. Choose English
  3. Show entry screen (Admin vs Member)
  4. Login as admin / admin123
  5. Show dashboard + notifications
  6. Point to main menu

Do NOT explain SQL tables in detail (Rebecca).
Do NOT explain member CRUD (Sonia).

------------------------------------------------------------
2. REBECCA (Database) — 1.5 minutes
------------------------------------------------------------
Files you made:
  database.sql
  database.py

What to say:
  "I designed the MySQL database called umuganda_sync.

   Tables:
   - admins        → login accounts
   - members       → community people
   - attendance    → who came on which date (linked to members)
   - projects      → community projects (can have a leader from members)
   - tools         → inventory
   - tool_borrows  → who borrowed which tool

   I used primary keys and foreign keys so attendance cannot point to
   a member that does not exist.

   database.py is the connection file.
   Everyone imports my functions instead of writing their own connect code.
   My main function is run_query for SELECT, INSERT, UPDATE, DELETE."

Demo:
  Show database.sql briefly (tables).
  Or run: python3 database.py
  Say "SUCCESS: connected..."

------------------------------------------------------------
3. JOSHUA (Members) — 1 minute
------------------------------------------------------------
File you made:
  members.py

What to say:
  "I built member management.

   The Village Leader can:
   - Add a member
   - View all members
   - Search by ID, name, or phone
   - Update details
   - Delete (with confirmation)
   - Deactivate or reactivate

   I reject empty names and duplicate phone numbers.
   Other modules call my function member_exists() to check IDs."

Demo:
  Main menu → 1 Members → 2 View All
  Optional: Search by phone 0788000001

------------------------------------------------------------
4. CYNTHIA (Attendance) — 1.5 minutes
------------------------------------------------------------
File you made:
  attendance.py

What to say:
  "I built attendance.

   We can record one person, or do a village roll call so every active
   member is marked and nobody is forgotten on paper.

   I also calculate attendance percentage and analytics:
   most active members, poor attendance, people with many absences.

   Option 9 is the lifetime participation summary.
   Members can also enter from the start screen with ID + phone
   and see only their own summary through my functions."

Demo:
  Main menu → 2 Attendance → 9
  Enter Member ID 1
  Show percentage + history

  OR mention menu 8 = whole village roll call

------------------------------------------------------------
5. SONIA (Projects) — 1.5 minutes
------------------------------------------------------------
File you made:
  projects.py

What to say:
  "I built community project management.

   Leaders can register a project, assign a leader member,
   update progress percent, mark completed, and delete.

   My module also finds overdue projects:
   expected end date already passed but status is still Pending or Ongoing.

   Friend's notifications use my overdue functions."

Demo:
  Main menu → 3 Projects → 2 View All
  Then → 5 View Overdue Projects

------------------------------------------------------------
6. ROSETTE (Tools / Inventory) — 1.5 minutes
------------------------------------------------------------
File you made:
  tools.py

What to say:
  "I built tool inventory.

   We register tools, update quantities, and track condition
   (Good, Needs Repair, Broken, Lost).

   Borrow reduces available stock.
   Return increases stock again.
   We keep history in tool_borrows.

   If available quantity is low, we show a warning.
   Broken or Lost tools cannot be borrowed."

Demo:
  Main menu → 4 Tool Inventory → 2 View All
  Point to LOW STOCK flag
  Optional: 7 Low Stock Warning or 8 Borrow History

------------------------------------------------------------
7. MARVELLA (Reports + Docs) — 1.5 minutes
------------------------------------------------------------
Files you made:
  reports.py
  docs/ (INSTALLATION, TESTING, USER_MANUAL, PRESENTATION, etc.)

What to say:
  "I built reports using MySQL aggregate queries:
   COUNT, SUM, AVG, GROUP BY, ORDER BY, and JOINs.

   Reports answer leader questions fast:
   - How many active members?
   - Who is most active?
   - Who has poor attendance?
   - Project summary by status
   - Inventory and currently borrowed tools
   - Attendance by village

   I also wrote documentation and the testing checklist
   so the team and lecturer can install and verify the system."

Demo:
  Main menu → 5 Reports → 1 Community Summary
  Then quickly → 4 Most Active Members

------------------------------------------------------------
8. FRIEND — Closing (30–45 seconds)
------------------------------------------------------------
What to say:
  "Together we replaced paper Umuganda records with a working Version 1.0.
   Seven people, seven modules, one MySQL database, connected through main.py.
   Thank you."

------------------------------------------------------------
QUICK DEMO ACCOUNTS
------------------------------------------------------------
Admin:
  username: admin
  password: admin123

Member entry (different from admin):
  National ID: 1199780123456789
  Phone: 0788000001

Member demo 2 (absences):
  National ID: 1199680123456791
  Phone: 0788000003

------------------------------------------------------------
IF LECTURER ASKS "WHO WROTE X?"
------------------------------------------------------------
main/menu/login/languages/dashboard  → Friend
database.sql / database.py           → Rebecca
members.py                           → Joshua
attendance.py                        → Cynthia
projects.py                          → Sonia
tools.py                             → Rosette
reports.py / docs                    → Marvella
