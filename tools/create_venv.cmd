@ECHO OFF
SETLOCAL ENABLEEXTENSIONS



REM ----------------------------------------------------------------------------------------------------
REM Necessary Files:
REM - pre_setup_scripts.txt
REM - required_personal_packages.txt
REM - required_misc.txt
REM - required_Qt.txt
REM - required_from_github.txt
REM - required_test.txt
REM - required_dev.txt
REM - post_setup_scripts.txt
REM ----------------------------------------------------------------------------------------------------


SET PROJECT_NAME=%~1
SET PROJECT_AUTHOR=%~2

SET TOOLS_FOLDER=%~dp0
SET WORKSPACE_FOLDER=%TOOLS_FOLDER%\..


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
SET TIMEBLOCK=%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%

ECHO ***************** Current time is *****************
ECHO                     %TIMEBLOCK%

ECHO ################# CHANGING DIRECTORY to -- %TOOLS_FOLDER% -- +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CD %TOOLS_FOLDER%
ECHO.

ECHO -------------------------------------------- PRE-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\pre_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A with %%B --------------^>
CALL %%A %%B
ECHO.
)


rem ECHO.
rem ECHO -------------------------------------------- Clearing Pip Cache --------------------------------------------
rem RD /S /Q %LocalAppData%\pip\Cache
rem ECHO.



ECHO -------------------------------------------- BASIC VENV SETUP --------------------------------------------
ECHO.


ECHO ################# Removing old venv folder
rem Icacls %WORKSPACE_FOLDER%\.venv /T /Q

%TOOLS_FOLDER%\delete_venv.py
ECHO.
ECHO %ERRORLEVEL%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%


ECHO ################# pycleaning workspace
call pyclean %WORKSPACE_FOLDER%
echo.



ECHO ################# creating new venv folder
mkdir %WORKSPACE_FOLDER%\.venv
ECHO.

ECHO ################# Calling venv module to initialize new venv
python -m venv %WORKSPACE_FOLDER%\.venv
ECHO.

ECHO ################# activating venv for package installation
CALL %WORKSPACE_FOLDER%\.venv\Scripts\activate.bat
ECHO.


ECHO ################# upgrading venv for package installation

call %WORKSPACE_FOLDER%\.venv\Scripts\python.exe -m pip install --upgrade pip

ECHO.

ECHO.
ECHO -------------------------------------------------------------------------------------------------------------
ECHO ++++++++++++++++++++++++++++++++++++++++++++ INSTALLING PACKAGES ++++++++++++++++++++++++++++++++++++++++++++
ECHO -------------------------------------------------------------------------------------------------------------
ECHO.
ECHO.



ECHO +++++++++++++++++++++++++++++ Standard Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

ECHO ################# Installing Setuptools
CALL pip install --no-cache-dir --upgrade setuptools
ECHO.

ECHO ################# Installing wheel
CALL pip install --no-cache-dir --upgrade wheel
ECHO.

ECHO ################# Installing PEP517
CALL pip install --no-cache-dir --upgrade PEP517
ECHO.

ECHO ################# Installing python-dotenv
CALL pip install --no-cache-dir --upgrade python-dotenv
ECHO.



ECHO ################# Installing flit
CALL pip install --no-cache-dir --upgrade flit
ECHO.




ECHO.

ECHO +++++++++++++++++++++++++++++ Gid Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\required_personal_packages.txt) do (
ECHO.
ECHO -------------------------- Installing %%B --------------^>
ECHO.
PUSHD %%A
CALL flit install -s
POPD
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Misc Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.
CALL pip install --upgrade --no-cache-dir -r .\venv_setup_settings\required_misc.txt
ECHO.


ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Experimental Packages +++++++++++++++++++++++++++++
ECHO.

ECHO.
CALL pip install --upgrade --no-cache-dir -r .\venv_setup_settings\required_experimental.txt
ECHO.

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ GUI Packages +++++++++++++++++++++++++++++
ECHO.

ECHO.
CALL pip install --upgrade --no-cache-dir -r .\venv_setup_settings\required_gui.txt
ECHO.


ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Packages From Github +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_from_github.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
CALL pip install --upgrade --no-cache-dir git+%%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Test Packages +++++++++++++++++++++++++++++
ECHO.

ECHO.
CALL pip install --upgrade --no-cache-dir -r .\venv_setup_settings\required_test.txt
ECHO.


ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Dev Packages +++++++++++++++++++++++++++++
ECHO.

ECHO.
CALL pip install --upgrade --no-cache-dir -r .\venv_setup_settings\required_dev.txt
ECHO.


ECHO.
ECHO.


ECHO -------------------------------------------- INSTALL THE PROJECT ITSELF AS -DEV PACKAGE --------------------------------------------
echo.
PUSHD %WORKSPACE_FOLDER%
rem call pip install -e .
call flit install -s
echo.
POPD
ECHO.

ECHO.
ECHO.

ECHO -------------------------------------------- POST-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\post_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A --------------^>
CALL %%A
ECHO.
)

call pip list | installed_packages_to_json.py

ECHO.
ECHO.

ECHO.
ECHO #############################################################################################################
ECHO -------------------------------------------------------------------------------------------------------------
ECHO #############################################################################################################
ECHO.
ECHO.
ECHO ++++++++++++++++++++++++++++++++++++++++++++++++++ FINISHED +++++++++++++++++++++++++++++++++++++++++++++++++
ECHO.
echo ************************** ErrorLevel at end of create_venv script is %ERRORLEVEL% **************************
ECHO.
ECHO #############################################################################################################
ECHO -------------------------------------------------------------------------------------------------------------
ECHO #############################################################################################################
ECHO.
