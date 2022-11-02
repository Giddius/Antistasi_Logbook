@ECHO off
SETLOCAL EnableDelayedExpansion
SET _THIS_FILE_DIR=%~dp0
SET _INPATH=%~dp1
SET _INFILE=%~nx1
SET _INFILEBASE=%~n1

REM ---------------------------------------------------
SET _date=%DATE:/=-%
SET _time=%TIME::=%
SET _time=%_time: =0%
REM ---------------------------------------------------
REM ---------------------------------------------------
SET _decades=%_date:~-2%
SET _years=%_date:~-4%
SET _months=%_date:~3,2%
SET _days=%_date:~0,2%
REM ---------------------------------------------------
SET _hours=%_time:~0,2%
SET _minutes=%_time:~2,2%
SET _seconds=%_time:~4,2%
REM ---------------------------------------------------
SET _TIMEBLOCK=%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%
SET _TIMEBLOCK_TIME=%_hours%-%_minutes%-%_seconds%
SET _TIMEBLOCK_DATE=%_years%-%_months%-%_days%


SET _SCRIPT_PATH=%_THIS_FILE_DIR%sqlite3_analyzer.exe

SET _OUTPUT_FILE=%_THIS_FILE_DIR%db_analysed.txt

SET _DB_FILE=%_THIS_FILE_DIR%..\antistasi_logbook\storage\storage.logbook_db


CALL %_SCRIPT_PATH% %_DB_FILE%>%_OUTPUT_FILE%