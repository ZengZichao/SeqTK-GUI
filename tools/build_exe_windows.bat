@echo off
rem Build the single-file Windows executable into dist\SeqTK-GUI.exe
rem Usage: tools\build_exe_windows.bat
rem Set ONEFILE=0 first to produce a folder build instead.
setlocal
cd /d "%~dp0\.."

where python >nul 2>nul || (echo [ERROR] python is not on PATH & exit /b 2)

python -c "import PyInstaller" 2>nul
if errorlevel 1 (
  echo [1/3] installing pyinstaller...
  python -m pip install pyinstaller || (echo [ERROR] pip install pyinstaller failed & exit /b 1)
)

if not exist "bin\windows\seqtk.exe" (
  echo [WARN] bin\windows\seqtk.exe is missing. Run
  echo        tools\seqtk-build\build_seqtk_windows.bat ..\seqtk-1.5
  echo        first, or the exe will ask the user to locate seqtk.
)

echo [2/3] packaging...
python -m PyInstaller --noconfirm --clean packaging\SeqTK-GUI.spec
if errorlevel 1 (echo [ERROR] PyInstaller failed & exit /b 1)

echo [3/3] result:
if exist "dist\SeqTK-GUI.exe" (
  for %%F in ("dist\SeqTK-GUI.exe") do echo   dist\SeqTK-GUI.exe  %%~zF bytes
) else (
  dir /b dist
)
echo Done. First launch unpacks to a temp folder and may take a few seconds.
