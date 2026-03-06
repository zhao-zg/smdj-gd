@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Usage:
REM   release-tag.bat 1.2.3
REM   release-tag.bat v1.2.3

if "%~1"=="" (
  for /f "delims=" %%V in ('node -p "require('./app_config.json').version"') do set "CUR_VER=%%V"
  echo Current version: !CUR_VER!
  set /p "INPUT_VER=Enter new version (e.g. 1.2.3): "
  if "!INPUT_VER!"=="" (
    echo No version entered. Aborted.
    exit /b 1
  )
) else (
  set "INPUT_VER=%~1"
)
set "TAG=%INPUT_VER%"

if /I not "%TAG:~0,1%"=="v" set "TAG=v%TAG%"

set "RAW_VER=%TAG:~1%"
set "MAJOR="
set "MINOR="
set "PATCH="
set "EXTRA="

for /f "tokens=1-4 delims=." %%a in ("%RAW_VER%") do (
  set "MAJOR=%%a"
  set "MINOR=%%b"
  set "PATCH=%%c"
  set "EXTRA=%%d"
)

if "%MAJOR%"=="" goto :invalid_version
if "%MINOR%"=="" goto :invalid_version
if "%PATCH%"=="" goto :invalid_version
if not "%EXTRA%"=="" goto :invalid_version

for %%V in ("%MAJOR%" "%MINOR%" "%PATCH%") do (
  set "SEG=%%~V"
  for /f "delims=0123456789" %%X in ("!SEG!") do goto :invalid_version
)

goto :version_ok

:invalid_version
  echo Invalid version format: %INPUT_VER%
  echo Required format: ^<major^>.^<minor^>.^<patch^> or v^<major^>.^<minor^>.^<patch^>
  exit /b 1

:version_ok

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo Current directory is not a git repository.
  exit /b 1
)

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  echo Missing git remote: origin
  exit /b 1
)

echo Fetching tags from origin...
git fetch --tags origin
if errorlevel 1 (
  echo Failed to fetch tags from origin.
  exit /b 1
)

git rev-parse -q --verify "refs/tags/%TAG%" >nul 2>nul
if not errorlevel 1 (
  echo Tag %TAG% already exists, removing...
  git tag -d "%TAG%" >nul 2>nul
  git push origin ":refs/tags/%TAG%" >nul 2>nul
)

echo Updating app_config.json version to %RAW_VER%...
node -e "const fs=require('fs'),f='app_config.json',o=JSON.parse(fs.readFileSync(f,'utf8'));o.version='%RAW_VER%';fs.writeFileSync(f,JSON.stringify(o,null,2)+'\n','utf8');"
if errorlevel 1 (
  echo Failed to update app_config.json.
  exit /b 1
)

git add app_config.json
git commit -m "chore: bump version to %RAW_VER%"
if errorlevel 1 (
  echo Failed to commit version bump.
  exit /b 1
)

echo Pushing version bump commit...
git push origin HEAD
if errorlevel 1 (
  echo Failed to push commit. Rolling back...
  git reset --soft HEAD~1
  git restore app_config.json
  exit /b 1
)

echo Creating tag %TAG% on current HEAD...
git tag -a "%TAG%" -m "Release %TAG%"
if errorlevel 1 (
  echo Failed to create tag.
  exit /b 1
)

echo Pushing tag %TAG% to origin...
git push origin "%TAG%"
if errorlevel 1 (
  echo Failed to push tag. Rolling back local tag...
  git tag -d "%TAG%" >nul 2>nul
  exit /b 1
)

echo Done. Triggered release workflow with tag: %TAG%
endlocal
exit /b 0
