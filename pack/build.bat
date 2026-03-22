@echo off
REM RagHubMCP Build Script for Windows
REM Go + PyInstaller hybrid packaging

setlocal EnableDelayedExpansion

echo ================================================
echo   RagHubMCP Build Script (Windows)
echo ================================================
echo.

REM Get version from version.txt
set VERSION=
for /f "tokens=*" %%i in (..\version.txt) do set VERSION=%%i
if "%VERSION%"=="" set VERSION=0.0.0
echo Version: %VERSION%

REM Build timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set BUILD_TIME=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%
echo Build Time: %BUILD_TIME%

REM Check prerequisites
echo.
echo Checking prerequisites...

REM Check Go
where go >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Go not found. Please install Go 1.21+
    exit /b 1
)
echo [OK] Go found

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)
echo [OK] Python found

REM Check PyInstaller
python -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo WARNING: PyInstaller not found. Installing...
    python -m pip install pyinstaller
)
echo [OK] PyInstaller ready

echo.
echo ================================================
echo   Step 1: Building Frontend
echo ================================================
echo.

cd ..\frontend
if %ERRORLEVEL% neq 0 (
    echo ERROR: Cannot find frontend directory
    exit /b 1
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

REM Build frontend
echo Building Vue frontend...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: Frontend build failed
    exit /b 1
)

echo [OK] Frontend built successfully
cd ..\pack

echo.
echo ================================================
echo   Step 2: Preparing Embed Resources
echo ================================================
echo.

cd go

REM Create embed directories in pack/go/
if not exist "frontend" mkdir frontend
if not exist "backend" mkdir backend
if not exist "data" mkdir data

REM Copy frontend dist to pack/go/frontend/dist
echo Copying frontend dist...
if exist "..\..\frontend\dist" (
    if exist "frontend\dist" rmdir /S /Q frontend\dist
    xcopy /E /I /Y ..\..\frontend\dist frontend\dist
    echo [OK] Frontend copied to pack/go/frontend/dist
) else (
    echo [WARN] Frontend dist not found, creating placeholder
    echo. > frontend\.gitkeep
)

REM Copy backend source to pack/go/backend/
echo Copying backend source...
if exist "backend\src" rmdir /S /Q backend\src
xcopy /E /I /Y ..\..\backend\src backend\src
copy /Y ..\..\backend\config.yaml backend\
copy /Y ..\..\backend\pyproject.toml backend\
echo [OK] Backend copied to pack/go/backend

REM Copy/prepare data directory
echo Preparing data directory...
if exist "..\..\data" (
    if exist "data" rmdir /S /Q data
    xcopy /E /I /Y ..\..\data data
    echo [OK] Data copied
) else (
    if not exist "data\flashrank_cache" mkdir data\flashrank_cache
    if not exist "data\chroma" mkdir data\chroma
    echo [OK] Data directories created
)

REM Create placeholder for models download script
if not exist "data\download_models.py" (
    echo # Download Rerank models on first run > data\download_models.py
    echo # Models will be downloaded to data/flashrank_cache/ >> data\download_models.py
)

cd ..

echo.
echo ================================================
echo   Step 3: Running Go Tests
echo ================================================
echo.

cd go

echo Running Go unit tests...
go test ./... -v -short
if %ERRORLEVEL% neq 0 (
    echo WARNING: Some tests failed, but continuing with build
)

echo [OK] Tests completed

echo.
echo ================================================
echo   Step 4: Building Go Wrapper
echo ================================================
echo.

REM Download dependencies
echo Downloading Go dependencies...
go mod download
go mod tidy

REM Build with version info
set LDFLAGS=-s -w -X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%

echo Building Windows executable...
go build -ldflags="%LDFLAGS%" -o ..\..\dist\RHM.exe .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Go build failed
    exit /b 1
)

echo [OK] Go wrapper built: RHM.exe
cd ..

echo.
echo ================================================
echo   Step 5: Building Python Package (Optional)
echo ================================================
echo.

REM This step is optional - the Go wrapper can use system Python
REM If you want to embed Python, run this:

REM cd python
REM python -m PyInstaller RHM.spec --clean
REM cd ..

echo.
echo ================================================
echo   Build Complete!
echo ================================================
echo.
echo Output files:
echo   - dist\RHM.exe (Go wrapper)
echo   - pack\go\frontend\  (Frontend embed)
echo   - pack\go\backend\   (Backend embed)  
echo   - pack\go\data\      (Data embed)
echo.

echo To test:
echo   dist\RHM.exe --version
echo   dist\RHM.exe --help
echo   dist\RHM.exe --no-browser --no-tray
echo.

echo To run tests:
echo   cd pack\go && go test ./... -v
echo.

endlocal