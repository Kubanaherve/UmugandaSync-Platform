# UmugandaSync — User Manual: Reports

## Overview

The Reports menu gives village leaders live statistics from MySQL and
optional text exports under `exports/`.

Open **Reports** from the main menu after admin login.

## Menu options

| # | Report | What you see |
| --- | --- | --- |
| 1 | Community summary | Members, projects, tools, Umuganda days, completion rate |
| 2 | Member report | Counts by status and village |
| 3 | Attendance summary | Present / Absent / Late / Excused + present-late rate |
| 4 | Most active members | Top 10 by Present/Late |
| 5 | Poor attendance | Members with 2+ absences |
| 6 | Project summary | Status averages, incomplete list, overdue list |
| 7 | Inventory summary | Stock, condition, low stock, open borrows |
| 8 | Attendance by village | Village-level present/absent totals |
| 9 | Export community summary | Writes `exports/community_summary_*.txt` |
| 10 | Export project summary | Writes `exports/project_summary_*.txt` |
| 11 | KPI snapshot | Compact operational indicators |
| 12 | Export attendance summary | Writes `exports/attendance_summary_*.txt` |
| 13 | Export community CSV | Writes `exports/community_summary_*.csv` |
| 0 | Back | Returns to the main menu |

## Tips

- Exports never overwrite each other; filenames include a timestamp.
- Empty tables show friendly “No data” messages instead of crashing.
- Overdue projects are active projects with `expected_end_date` before today.

## Related docs

- [Architecture](ARCHITECTURE.md)
- [Testing](TESTING.md)
- [Installation](INSTALLATION.md)
## Presentation tip

Demo options 1, 6, 11, and 13 for a complete leader workflow.
