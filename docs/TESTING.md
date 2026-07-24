# UmugandaSync — Testing Guide

## Purpose
This checklist verifies that the reports module (and the overall
system it depends on) works correctly before presentation.

## Pre-Test Setup
- [ ] MySQL server is running
- [ ] database.sql has been imported successfully
- [ ] config.py has correct connection details
- [ ] At least a few sample rows exist in members, attendance,
      projects, and tools (for reports to show real numbers)

## Reports Module Test Cases

1. Community Summary
   - [ ] Run Reports → 1
   - [ ] Confirm total members, active members, total/ongoing
         projects, tool types, available tool units, and
         umuganda dates recorded all display without errors
   - [ ] Confirm numbers match what's actually in the database

2. Member Report
   - [ ] Run Reports → 2
   - [ ] Confirm members are grouped correctly by status
   - [ ] Confirm members are grouped correctly by village

3. Attendance Summary
   - [ ] Run Reports → 3
   - [ ] Confirm attendance counts by status display correctly
   - [ ] Confirm overall present/late percentage calculates correctly

4. Most Active Members
   - [ ] Run Reports → 4
   - [ ] Confirm top 10 list is sorted by present/late count,
         highest first

5. Poor Attendance Members
   - [ ] Run Reports → 5
   - [ ] Confirm only members with 2+ absences appear
   - [ ] Confirm sorted by absent count, highest first

6. Project Summary
   - [ ] Run Reports → 6
   - [ ] Confirm project counts and average progress by status
   - [ ] Confirm incomplete projects list shows correct due dates

7. Inventory Summary
   - [ ] Run Reports → 7
   - [ ] Confirm tool totals, condition breakdown, low-stock list,
         and currently-borrowed list all display correctly

8. Attendance by Village
   - [ ] Run Reports → 8
   - [ ] Confirm records/present-late/absent counts per village

## Edge Cases
- [ ] Empty database (no members/attendance/projects/tools) does
      not crash any report — shows "No data" messages instead
- [ ] Reports menu option 0 exits back to the main menu correctly
- [ ] Invalid menu input (e.g. letters) shows "Invalid choice."
      without crashing

## Sign-off
Tested by: Marvella
Date: _______________
Result: Pass / Fail (circle one)
