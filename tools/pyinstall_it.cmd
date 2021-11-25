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

call pskill64 Dropbox
call pyclean ..\
rem --upx-dir "D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64" ^
rem --upx-exclude "vcruntime140.dll" ^
set WORKSPACEDIR=D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook
set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
cd %_THIS_FILE_DIR%\..
call .venv\Scripts\activate.bat
set _CONFIG_FILE=tools\_project_devmeta.env
for /f %%i in (%CONFIG_FILE%) do set %%i
set _OUT_DIR=%WORKSPACEDIR%\pyinstaller_output\%_TIMEBLOCK_DATE%
RD /S /Q %WORKSPACEDIR%\pyinstaller_output\%_TIMEBLOCK_DATE%
mkdir %_OUT_DIR%
cd %INPATH%


rem options: onedir OR onefile
set _TYPE_TO_GENERATE=onefile

rem options: console OR windowed
set _TYPE_OF_UI=console

set _NAME_OF_APPLICATION=Antistasi_Logbook

set _ICON=D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Gid_Scratches\gid_scratch\pyinstaller_scratch\anwendung.ico


set PYTHONOPTIMIZE=1
call pyinstaller ^
--clean ^
--noconfirm ^
--log-level=INFO ^
--%_TYPE_TO_GENERATE% ^
--%_TYPE_OF_UI% ^
--paths %WORKSPACEDIR% ^
--hiddenimport distutils ^
--hiddenimport tzlocal ^
--icon %_ICON% ^
--name %_NAME_OF_APPLICATION% ^
--upx-dir D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64 ^
--upx-exclude vcruntime140.dll ^
--upx-exclude ucrtbase.dll ^
--distpath %_OUT_DIR%\dist ^
--workpath %_OUT_DIR%\work ^
--specpath %_OUT_DIR%\spec ^
D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\Antistasi_Logbook.spec