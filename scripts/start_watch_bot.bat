@echo off
REM Double-click to turn the watch bot ON. It runs continuously, checking
REM every 6 hours by default, until you close this window or press Ctrl+C
REM (that's how you turn it OFF).
REM
REM Findings land in the scraped_updates\ folder (page changes) and in
REM /admin/newsletter/contentitem/ (drafts, from both RSS and page sources).

call "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0..\manage.py" run_watch_bot
