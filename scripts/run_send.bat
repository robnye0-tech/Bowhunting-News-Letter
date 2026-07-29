@echo off
REM Run from Windows Task Scheduler to send the weekly newsletter.
REM Set the "Start in" field of the scheduled task to the project's root folder.
REM Run this AFTER reviewing/approving content items for the week in /admin.

call "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0..\manage.py" send_weekly_newsletter
