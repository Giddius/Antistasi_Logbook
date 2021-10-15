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

for /f %%i in (%_THIS_FILE_DIR%_project_devmeta.env) do set %%i

autoflake.exe -i --imports=googletrans,Jinja2,checksumdir,click,regex,parce,fuzzywuzzy,python-Levenshtein,Pillow,PyGithub,WeasyPrint,discord.py,url-normalize,async-property,watchgod,pdfkit,pytz,google-auth,google_api_python_client,google_auth_oauthlib,psutil,cchardet,python-benedict,udpy,commonmark,pyfiglet,graphviz,pydot,lxml,networkx,pyowm,colormap,aiosqlite,discord-flags,paramiko,antistasi_template_checker,cryptography,humanize,marshmallow,parse,invoke,arrow,pendulum,python-dateutil,dateparser --expand-star-imports --ignore-init-module-imports --exclude=**/dev_tools_and_scripts -r %TOPLEVELMODULE%