@rem taskarg: ${file}
@Echo off
SETLOCAL EnableDelayedExpansion

SET THIS_FOLDER=%~dp0

SET _NAME=Antistasi_Logbook

SET _CREATE_TYPE=onefile
rem SET _CREATE_TYPE=onedir


rem --upx-dir "D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64" ^
rem --upx-exclude "vcruntime140.dll" ^

set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
pushd %THIS_FOLDER%\..
RD /S /Q %THIS_FOLDER%\..\pyinstaller_output_%_NAME%
mkdir %THIS_FOLDER%\..\pyinstaller_output_%_NAME%

set PYTHONOPTIMIZE=1
pyinstaller --clean --noconfirm --log-level=INFO --onefile ^
-n %_NAME% ^
--upx-dir D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64 ^
--upx-exclude vcruntime140.dll ^
--upx-exclude ucrtbase.dll ^
--distpath %THIS_FOLDER%\..\pyinstaller_output_%_NAME%/dist ^
--workpath %THIS_FOLDER%\..\pyinstaller_output_%_NAME%/work ^
%INPATH%%INFILE%