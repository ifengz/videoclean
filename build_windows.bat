@echo off
setlocal
cd /d "%~dp0"

if not exist ffmpeg mkdir ffmpeg

if not "%~1"=="" (
  if exist "%~1\ffmpeg.exe" (
    copy /Y "%~1\ffmpeg.exe" "ffmpeg\ffmpeg.exe" >nul
  ) else if exist "%~1" (
    copy /Y "%~1" "ffmpeg\ffmpeg.exe" >nul
  ) else (
    echo [ERROR] 传入的 ffmpeg 路径不存在：%~1
    exit /b 1
  )
)

if not exist ffmpeg\ffmpeg.exe (
  echo [ERROR] 缺少 ffmpeg\ffmpeg.exe
  echo [ERROR] 用法1：先把 ffmpeg.exe 放到项目的 ffmpeg\ 目录下，再运行 build_windows.bat
  echo [ERROR] 用法2：直接运行 build_windows.bat "D:\ffmpeg\bin\ffmpeg.exe"
  exit /b 1
)

py -3 -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --name VideoCleaner ^
  --add-data "ffmpeg;ffmpeg" ^
  app.py

if errorlevel 1 (
  echo [ERROR] 打包失败
  exit /b 1
)

echo [OK] 打包完成：dist\VideoCleaner
echo [OK] 打包目录已包含 ffmpeg，可直接发整个 dist\VideoCleaner
