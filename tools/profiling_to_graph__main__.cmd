@rem taskarg: ${file}
@Echo off
set OLDHOME_FOLDER=%~dp0
pushd %OLDHOME_FOLDER%
call ..\.venv\Scripts\activate
rem call profiling_to_graph.cmd ..\src\__main__.py
call profiling_to_graph.cmd D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\GidAppTools\gidapptools\meta_data\interface.py
