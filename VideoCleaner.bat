@echo off
setlocal
cd /d "%~dp0"

if /I "%~1"=="build" goto :build
goto :run

:run
if not exist output mkdir output

if exist "%~dp0python\python.exe" (
  "%~dp0python\python.exe" app.py
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 app.py
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python app.py
  exit /b %errorlevel%
)

echo [ERROR] 找不到 Python。
echo [ERROR] 用法：
echo [ERROR] 1. 直接运行：双击本文件启动
echo [ERROR] 2. 构建目录版：VideoCleaner.bat build
echo [ERROR] 3. 带便携 Python 构建：VideoCleaner.bat build "D:\portable-python"
pause
exit /b 1

:build
set DIST_DIR=dist-bat\VideoCleaner-BAT

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\video_cleaner"
mkdir "%DIST_DIR%\ffmpeg"
mkdir "%DIST_DIR%\output"

copy /Y app.py "%DIST_DIR%\app.py" >nul
copy /Y "VideoCleaner.bat" "%DIST_DIR%\VideoCleaner.bat" >nul
copy /Y README.md "%DIST_DIR%\README.md" >nul
copy /Y ffmpeg\ffmpeg.exe "%DIST_DIR%\ffmpeg\ffmpeg.exe" >nul
copy /Y video_cleaner\__init__.py "%DIST_DIR%\video_cleaner\__init__.py" >nul
copy /Y video_cleaner\core.py "%DIST_DIR%\video_cleaner\core.py" >nul

if not "%~2"=="" (
  if exist "%~2\python.exe" (
    mkdir "%DIST_DIR%\python"
    xcopy /E /I /Y "%~2" "%DIST_DIR%\python" >nul
  ) else (
    echo [WARN] 便携 Python 路径无效：%~2
  )
)

echo [OK] 已生成目录版：%DIST_DIR%
echo [OK] 团队双击 %DIST_DIR%\VideoCleaner.bat 即可启动
if exist "%DIST_DIR%\python\python.exe" (
  echo [OK] 已一起带上便携 Python
) else (
  echo [WARN] 当前目录版未包含 Python，团队电脑需要有 py 或 python 命令
)
