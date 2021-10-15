@rem taskarg: ${file}
@Echo off
SETLOCAL EnableDelayedExpansion


rem --upx-dir "D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64" ^
rem --upx-exclude "vcruntime140.dll" ^

set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
pushd %INPATH%
mkdir %INPATH%pyinstaller_output_%INFILEBASE%

set PYTHONOPTIMIZE=1
pyinstaller --clean --noconfirm --log-level=INFO --onefile -c ^
-i D:\Dropbox\hobby\Modding\Ressources\Icons\To_Sort_Icons\ico_icons\Antistasi_flag_experiment.ico ^
-n %2 ^
--upx-dir D:\Dropbox\hobby\Modding\Ressources\python\upx\upx-3.96-win64 ^
--upx-exclude vcruntime140.dll ^
--upx-exclude ucrtbase.dll ^
--distpath %INPATH%pyinstaller_output_%INFILEBASE%/dist ^
--workpath %INPATH%pyinstaller_output_%INFILEBASE%/work ^
--specpath %INPATH%pyinstaller_output_%INFILEBASE%/spec ^
%INFILE%