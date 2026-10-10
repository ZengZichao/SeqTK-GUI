@echo off
rem Build bin\windows\seqtk.exe from an unmodified seqtk source tree.
rem Usage: build_seqtk_windows.bat [path\to\seqtk-1.5]
rem Requires a MinGW-w64 gcc on PATH with zlib available.
setlocal
set "SRC=%~1"
if "%SRC%"=="" set "SRC=..\..\..\seqtk-1.5"
if not exist "%SRC%\seqtk.c" (
  echo [ERROR] seqtk.c not found under "%SRC%"
  echo         pass the source directory as the first argument.
  exit /b 2
)

set "HERE=%~dp0"
set "OUT=%HERE%\..\..\bin\windows"
if not exist "%OUT%" mkdir "%OUT%"

rem Resolve the source tree once so the rewrite below has something to match.
for %%I in ("%SRC%") do set "SRCABS=%%~fI"
set "HEREN=%HERE:~0,-1%"

echo [1/2] compiling seqtk + MinGW PRNG shim...
rem This exe is published, so it must not carry the directory it was built in.
rem -g0 drops the debug records that store absolute paths; the prefix maps cover
rem the strings assert() keeps via __FILE__.
gcc -g0 -O2 -Wall -Wno-unused-function -Wno-format ^
    "-ffile-prefix-map=%SRCABS%=seqtk-1.5" ^
    "-ffile-prefix-map=%HEREN%=tools/seqtk-build" ^
    "%SRCABS%\seqtk.c" "%HERE%mingw_prng_shim.c" ^
    -o "%OUT%\seqtk.exe" -lz -lm
if errorlevel 1 (
  echo [ERROR] gcc failed. Install a MinGW-w64 toolchain with zlib,
  echo         or drop mingw_prng_shim.c if your libc already provides drand48.
  exit /b 1
)

echo [2/2] checking the result...
"%OUT%\seqtk.exe" 2>&1 | findstr /C:"Version:" || (
  echo [ERROR] the binary did not report a version.
  exit /b 1
)
rem Belt and braces: refuse to finish with a binary that names this machine.
findstr /M /C:"%SRCABS%" "%OUT%\seqtk.exe" >nul 2>nul && (
  echo [ERROR] the binary still embeds "%SRCABS%".
  exit /b 1
)
findstr /M /C:"%USERPROFILE%" "%OUT%\seqtk.exe" >nul 2>nul && (
  echo [ERROR] the binary still embeds "%USERPROFILE%".
  exit /b 1
)
echo OK: %OUT%\seqtk.exe
