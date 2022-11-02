@Echo off

SET TOOLS_FOLDER=%~dp0
cd %TOOLS_FOLDER%
cd ..
call .venv\Scripts\activate



call .venv\Scripts\python -m pip install --no-cache-dir --force-reinstall https://github.com/rogerbinns/apsw/releases/download/3.38.1-r1/apsw-3.38.1-r1.zip ^
--global-option=fetch ^
--global-option=--all ^
--global-option=build ^
--global-option=--enable-all-extensions