# UmugandaSync — Installation Guide

## Requirements
- Python 3.10+
- MySQL Server (running locally or accessible remotely)
- pip packages: mysql-connector-python (or PyMySQL, depending on database.py)

## Setup Steps

1. Clone the repository
   git clone https://github.com/Kubanaherve/UmugandaSync-OS.git
   cd UmugandaSync-OS

2. Install Python dependencies
   pip install mysql-connector-python

3. Create the MySQL database
   Log into MySQL and run the schema file:
   mysql -u root -p < database.sql

   This creates the `umuganda_sync` database with all tables:
   admins, members, attendance, projects, tools, tool_borrows

4. Configure database connection
   Open config.py and set your MySQL host, username, password,
   and database name to match your local setup.

5. Run the application
   python3 main.py

6. Log in
   Admin login:
     username: admin
     password: admin123

   Member login (view-only):
     Member ID: 1
     Phone: 0788000001

## Troubleshooting
- "Access denied" errors → check MySQL username/password in config.py
- "Unknown database" → make sure database.sql ran successfully
- Module not found → confirm mysql-connector-python is installed
  in the same Python environment you're running main.py with
