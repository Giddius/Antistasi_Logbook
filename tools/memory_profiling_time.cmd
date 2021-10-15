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
set SUB_OUTPUT_FOLDER=%BASE_OUTPUT_FOLDER%\%CLEANED_FILE_NAME%\memory_profiling

set "_FLAGS=--slope"

SET DECORATOR_HANDLING_SCRIPT=%OLDHOME_FOLDER%temp_modfiy_profile_decorators.py

SET CONVERT_SCRIPT_PATH=%OLDHOME_FOLDER%svg_to_png.py


SET FILE_PATH_BASE=%SUB_OUTPUT_FOLDER%\[%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%]%CLEANED_FILE_NAME%
SET FILE_PATH_SLOPE=%FILE_PATH_BASE%_SLOPE.svg
SET FILE_PATH_FLAME=%FILE_PATH_BASE%_FLAME.svg

pushd %INPATH%
mkdir %SUB_OUTPUT_FOLDER%
rem ECHO MODIFYNG FILE %INFILE% WITH DECORATORS
rem call %DECORATOR_HANDLING_SCRIPT% %FULLINPATH%
call mprof.exe clean
call mprof.exe run --include-children %~1

call mprof.exe plot -o %FILE_PATH_SLOPE% --slope --title "%INFILE% SLOPE" --backend svg
call mprof.exe plot -o %FILE_PATH_FLAME% --flame --title "%INFILE% FLAME" --backend svg
call mprof.exe clean
rem ECHO REVERTING MODIFICATIONS IN FILE %INFILE%
rem SET REVERSE_PROFILE_MODIFICATION=1
rem call %DECORATOR_HANDLING_SCRIPT% 1
call %CONVERT_SCRIPT_PATH% %FILE_PATH_SLOPE% %FILE_PATH_FLAME%

pushd %OLDHOME_FOLDER%

