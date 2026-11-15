@echo off
TITLE The Earth Information Jukebox - NASA Space Apps 2026
cd /d "%~dp0"
rem Use the Windows Python launcher (py) if it is installed, otherwise plain "python".
set PY=python
where py >nul 2>nul && set PY=py -3
echo Installing or checking the packages (first run takes a minute)...
%PY% -m pip install -q -r requirements.txt
echo.
echo Building the tracks from the NASA images...
%PY% build_tracks.py
echo.
echo Opening the jukebox at http://127.0.0.1:5000  (close this window to stop it)
start "" http://127.0.0.1:5000
%PY% app.py
pause
