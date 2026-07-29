@echo off
REM Run from Windows Task Scheduler to pull new draft content from RSS sources.
REM Set the "Start in" field of the scheduled task to the project's root folder.

call "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0..\manage.py" aggregate_content
