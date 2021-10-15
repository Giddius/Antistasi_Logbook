@rem taskarg: ${file}

@Echo off
set OLDHOME_FOLDER=%~dp0
pushd %OLDHOME_FOLDER%
call ..\.venv\Scripts\activate

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



SET FULLINPATH=%~1
set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
set _INEXTENSION=%~x1
SET INEXTENSION=%_INEXTENSION:~1%
SET CLEANED_FILE_NAME=%INFILEBASE%_%INEXTENSION%

set BASE_OUTPUT_FOLDER=%OLDHOME_FOLDER%reports
set SUB_OUTPUT_FOLDER=%BASE_OUTPUT_FOLDER%\%CLEANED_FILE_NAME%\text_profiling
mkdir %SUB_OUTPUT_FOLDER%
python -m cProfile -s cumtime %FULLINPATH% > %SUB_OUTPUT_FOLDER%\[%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%]_%CLEANED_FILE_NAME%.txt



