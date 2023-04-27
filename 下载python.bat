@echo off
setlocal enabledelayedexpansion

set "url=https://www.python.org/ftp/python/3.11.1/python-3.11.1-amd64.exe"
set "filename=python-3.11.1-amd64.exe"

echo Downloading %url% ...
powershell -command "Invoke-WebRequest %url% -OutFile %filename%"

echo Running %filename% ...
start "" /wait "%filename%"

echo Done.