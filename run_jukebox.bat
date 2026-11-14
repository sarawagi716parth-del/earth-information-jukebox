@echo off
TITLE The Earth Information Jukebox - NASA Space Apps 2026
echo ======================================================================
echo    THE EARTH INFORMATION JUKEBOX
echo    NASA Space Apps Challenge 2026 - Accessible Sonification Platform
echo ======================================================================
echo.
echo Launching Accessible Local Web Jukebox...
echo URL: http://localhost:8501
echo.
& "C:\Users\Parth\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py --server.headless false
pause
