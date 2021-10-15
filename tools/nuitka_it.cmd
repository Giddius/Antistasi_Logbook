@Echo off

set THIS_FILE_FOLDER=%~dp0
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
rem echo # created at --^> %TIMEBLOCK%

cd %THIS_FILE_FOLDER%
call ..\.venv\Scripts\activate.bat
cd %INPATH%
call nuitka --standalone ^
--windows-dependency-tool=pefile ^
--experimental=use_pefile_recurse ^
--experimental=use_pefile_fullrecurse ^
--plugin-enable=qt-plugins ^
--plugin-enable=numpy ^
D:\Dropbox\hobby\Modding\Projects\Giddis_Project_Creator\gidprojectcreator\__main__.py