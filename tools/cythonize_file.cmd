@rem taskarg: ${file}
@ECHO off
SETLOCAL EnableDelayedExpansion

SET _THIS_FILE_DIR=%~dp0
SET _INPATH=%~dp1
SET _INFILE=%~nx1
SET _INFILEBASE=%~n1

SET FULLINPATH=%~1

pushd %_THIS_FILE_DIR%
call ..\.venv\Scripts\activate


SET _BUILD_FOLDER=..\build

SET _C_FILE=%_INPATH%%_INFILEBASE%.c

call cythonize -i -f --3str %FULLINPATH%

RD /S /Q %_BUILD_FOLDER%

DEL %_C_FILE%
