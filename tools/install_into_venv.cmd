@Echo off


for /f "eol=; tokens=*" %%I in ('powershell Get-Clipboard') do set CLIPBOARD_TEXT=%%I

call ..\.venv\Scripts\activate
pip install %CLIPBOARD_TEXT%
pip freeze > ..\clipboard_installed_packages.txt

