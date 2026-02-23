@echo off
echo ========================================
echo Building WhatsApp Business Android APK
echo ========================================
echo.
echo This will take 3-5 minutes...
echo Please wait...
echo.

cd /d "%~dp0"

echo [1/3] Cleaning previous builds...
call gradlew.bat clean --no-daemon --console=plain

echo.
echo [2/3] Building debug APK...
call gradlew.bat assembleDebug --no-daemon --console=plain

echo.
if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo ========================================
    echo SUCCESS! APK built successfully!
    echo ========================================
    echo.
    echo Location: app\build\outputs\apk\debug\app-debug.apk
    echo Size:
    for %%A in ("app\build\outputs\apk\debug\app-debug.apk") do echo %%~zA bytes
    echo.
    echo [3/3] Opening APK location...
    explorer "app\build\outputs\apk\debug"
    echo.
    echo Transfer this file to your phone and install it!
    echo.
) else (
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
    echo Common solutions:
    echo 1. Make sure you have JDK 17 installed
    echo 2. Close Android Studio if it's running
    echo 3. Try running as Administrator
    echo.
)

pause
