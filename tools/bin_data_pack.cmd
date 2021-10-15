@echo off
setlocal enableextensions
set OLDHOME_FOLDER=%~dp0
set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1

rem ---------------------------------------------------
set _date=%DATE:/=-%
set _time=%TIME::=%
set _time=%_time: =0%
rem ---------------------------------------------------
rem ---------------------------------------------------
set _decades=%_date:~-2%
set _years=%_date:~-4%
set _months=%_date:~3,2%
set _days=%_date:~0,2%
rem ---------------------------------------------------
set _hours=%_time:~0,2%
set _minutes=%_time:~2,2%
set _seconds=%_time:~4,2%
rem ---------------------------------------------------
set TIMEBLOCK=%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%
Echo ################# Current time is %TIMEBLOCK%
cd %OLDHOME_FOLDER%
call ..\.venv\Scripts\activate
call %OLDHOME_FOLDER%private_quick_scripts\clean_data_pack.py
call appdata_binit -n %PROJECT_NAME% -a %PROJECT_AUTHOR% -64 -cz %TOPLEVELMODULE%\init_userdata -i oauth2_google_credentials.json -i token.pickle -i save_link_db.db -i save_suggestion.db -i archive/* -i performance_data/* -i stats/* -i last_shutdown_message.pkl