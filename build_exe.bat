@echo off
chcp 65001 >nul
echo ========================================
echo   写真GPS抽出ツール EXE作成スクリプト
echo ========================================
echo.

REM Pythonの確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    echo https://www.python.org/downloads/ からインストールしてください
    pause
    exit /b 1
)

echo [1/3] 必要なライブラリをインストール中...
pip install -r requirements.txt

if errorlevel 1 (
    echo [エラー] ライブラリのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo [2/3] EXEファイルを作成中...
pyinstaller --onefile --windowed --name "写真GPS抽出ツール" --add-data "README.md;." extract_photo_gps_gui.py

if errorlevel 1 (
    echo [エラー] EXEの作成に失敗しました
    pause
    exit /b 1
)

echo.
echo [3/3] 完了!
echo.
echo ========================================
echo EXEファイルが作成されました:
echo   dist\写真GPS抽出ツール.exe
echo ========================================
echo.
echo このEXEファイルを配布すれば、
echo Pythonがなくても誰でも使えます！
echo.

pause
