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


Echo.
ECHO -------------------------------------------- preparing venv_setup_settings --------------------------------------------
ECHO.
ECHO ################# preparing venv_setup_settings
call  %TOOLS_FOLDER%prepare_venv_settings.py %TOOLS_FOLDER%
if %ERRORLEVEL% == 1 (
    ECHO.
    ECHO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ECHO 8888888888888888888888888888888888888888888888888
    ECHO.
    Echo Created Venv settings folder, please custimize the files and restart the Scripts
    ECHO.
    ECHO 8888888888888888888888888888888888888888888888888
    ECHO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ECHO.
    Exit 63
) else (
    Echo finished preparing venv
)


rem ECHO.
rem ECHO -------------------------------------------- Clearing Pip Cache --------------------------------------------
rem RD /S /Q %LocalAppData%\pip\Cache
rem ECHO.



ECHO -------------------------------------------- BASIC VENV SETUP --------------------------------------------
ECHO.


ECHO ################# Removing old venv folder
RD /S /Q %WORKSPACE_FOLDER%\.venv
ECHO.


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

ECHO ################# upgrading pip to get rid of stupid warning
call curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
set _REPLACE_STRING=
call fart -C %TOOLS_FOLDER%get-pip.py "import os.path" "import setuptools\nimport os.path"
call get-pip.py --force-reinstall
del /Q get-pip.py
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

ECHO ################# Installing tomlkit
CALL pip install --no-cache-dir --upgrade tomlkit
ECHO.

ECHO ################# Installing invoke
CALL pip install --no-cache-dir --upgrade invoke
ECHO.

ECHO ################# Installing flit
CALL pip install --no-cache-dir --upgrade flit
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
