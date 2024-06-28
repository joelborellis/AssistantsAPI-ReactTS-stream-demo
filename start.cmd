@echo off

echo.
echo Restoring backend python packages
echo.
call python -m pip install -r requirements.txt
if "%errorlevel%" neq "0" (
    echo Failed to restore backend python packages
    exit /B %errorlevel%
)

echo.
echo Starting backend
echo.
start http://localhost:5000
call python ./server.py
if "%errorlevel%" neq "0" (
    echo Failed to start backend
    exit /B %errorlevel%
)