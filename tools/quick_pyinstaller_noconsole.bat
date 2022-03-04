@rem taskarg: ${file}
@Echo off
SETLOCAL EnableDelayedExpansion

SET THIS_FOLDER=%~dp0

SET _NAME=Antistasi_Logbook






rem --upx-dir "D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64" ^
rem --upx-exclude "vcruntime140.dll" ^
call %THIS_FOLDER%..\.venv\Scripts\activate
set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
pushd %THIS_FOLDER%\..
RD /S /Q %THIS_FOLDER%\..\pyinstaller_output_%_NAME%
mkdir %THIS_FOLDER%\..\pyinstaller_output_%_NAME%

set PYTHONOPTIMIZE=2
pyinstaller --clean --noconfirm --log-level=INFO ^
-n %_NAME% ^
--upx-dir D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64 ^
--upx-exclude vcruntime140.dll ^
--upx-exclude ucrtbase.dll ^
--distpath %THIS_FOLDER%\..\pyinstaller_output_%_NAME%/dist ^
--workpath %THIS_FOLDER%\..\pyinstaller_output_%_NAME%/work ^
%INPATH%%INFILE%


call 7z.exe a -tZip %THIS_FOLDER%\..\pyinstaller_output_%_NAME%\dist\%_NAME%.zip %THIS_FOLDER%\..\pyinstaller_output_%_NAME%\dist\%_NAME%\ -mx9