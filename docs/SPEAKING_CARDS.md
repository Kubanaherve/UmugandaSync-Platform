# SPEAKING CARDS — print or keep on phone

========================
FRIEND
========================
Files: main.py, menu.py, login.py, config.py, helpers.py,
       languages.py, dashboard.py, notifications.py, search.py

Say in 3 lines:
1. I connect all modules and handle language + admin/member entry.
2. Admin password login; member uses ID + phone.
3. Dashboard and warnings come from live MySQL counts.

Demo: start app → language → admin login → dashboard

========================
REBECCA
========================
Files: database.sql, database.py

Say in 3 lines:
1. I created umuganda_sync tables with primary/foreign keys.
2. attendance and borrows link to real members/tools.
3. database.py is the shared connection used by everyone.

Demo: show tables in database.sql OR python3 database.py

========================
SONIA
========================
File: members.py

Say in 3 lines:
1. I manage community members (add/view/search/update/delete).
2. I block duplicate phones and empty names.
3. Others use member_exists() from my file.

Demo: Members → View All / Search

========================
CYNTHIA
========================
File: attendance.py

Say in 3 lines:
1. I record attendance one-by-one or whole village roll call.
2. I calculate percentage and find poor attendance.
3. Members can see their lifetime participation summary.

Demo: Attendance → 9 summary for ID 1

========================
JOSHUA
========================
File: projects.py

Say in 3 lines:
1. I track community projects and progress %.
2. Leaders can mark completed or update status.
3. I detect overdue projects for notifications.

Demo: Projects → View All → Overdue

========================
ROSETTE
========================
File: tools.py

Say in 3 lines:
1. I manage tools and stock quantities.
2. Borrow and return update available stock.
3. Low stock and borrow history help stop lost tools.

Demo: Tools → View All → Low Stock

========================
MARVELLA
========================
Files: reports.py, docs/

Say in 3 lines:
1. I make reports with JOIN, COUNT, GROUP BY.
2. Leaders get summaries without counting paper.
3. I wrote install/testing docs for the team.

Demo: Reports → Community Summary → Most Active
