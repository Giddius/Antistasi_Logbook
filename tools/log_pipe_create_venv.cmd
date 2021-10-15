@echo off
SETLOCAL EnableDelayedExpansion

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:-------------------------------------

set OLDHOME_FOLDER=%~dp0
set LOG_FOLDER=%OLDHOME_FOLDER%create_venv_logs

RD /S /Q "%LOG_FOLDER%"

mkdir %LOG_FOLDER%

pushd %OLDHOME_FOLDER%


rem ++++++++++++++++++++++++++++++++++++++++++++++++
rem &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

SET PROJECT_NAME=ANTISTASI_LOGBOOK

rem -------------------------------------------------

SET PROJECT_AUTHOR=ANTISTASI_TOOLS

rem &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
rem ++++++++++++++++++++++++++++++++++++++++++++++++

create_venv.cmd %PROJECT_NAME% %PROJECT_AUTHOR% 2> "%LOG_FOLDER%\create_venv.errors" | TEE "%LOG_FOLDER%\create_venv.log"

if %ERRORLEVEL% == 0 (
    @echo off
    echo ErrorLevel is zero
    echo.
    echo No need to run again with combined log!!
) else (
   @echo off
   echo ErrorLevel is > 1
   echo.
   echo Running again with combined log to get error location
   echo.
   echo.
   call create_venv.cmd %PROJECT_NAME% %PROJECT_AUTHOR% > "%LOG_FOLDER%\create_venv_overall.log" 2>&1
)


