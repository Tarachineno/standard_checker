@echo off
setlocal enabledelayedexpansion

echo 🚀 Standard Version Checker ポータブル版を起動中...

REM スクリプトのディレクトリを取得
set SCRIPT_DIR=%~dp0

REM ポータブルPythonのパス設定
set PYTHON_PATH=%SCRIPT_DIR%python_portable\python.exe
set PYTHONPATH=%SCRIPT_DIR%standard_checker
set PATH=%SCRIPT_DIR%python_portable;%SCRIPT_DIR%python_portable\Scripts;%PATH%

REM Pythonの存在確認
if not exist "%PYTHON_PATH%" (
    echo ❌ ポータブルPythonが見つかりません。
    echo 以下の手順でPython Embeddable Packageをダウンロードしてください：
    echo 1. https://www.python.org/downloads/windows/ にアクセス
    echo 2. "Python 3.11.x - 2023-xx-xx" の "Windows embeddable package (64-bit)" をダウンロード
    echo 3. ダウンロードしたZIPファイルを解凍
    echo 4. 解凍したファイルを %SCRIPT_DIR%python_portable\ にコピー
    pause
    exit /b 1
)

REM 依存関係のインストール（初回のみ）
if not exist "%SCRIPT_DIR%packages\installed.flag" (
    echo 📦 依存関係をインストール中...
    
    REM pipを有効化
    if not exist "%SCRIPT_DIR%python_portable\Scripts\pip.exe" (
        echo 📥 pipをダウンロード中...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%SCRIPT_DIR%get-pip.py'"
        "%PYTHON_PATH%" "%SCRIPT_DIR%get-pip.py" --no-warn-script-location
        del "%SCRIPT_DIR%get-pip.py"
    )
    
    REM 依存関係をインストール
    "%PYTHON_PATH%" -m pip install --no-index --find-links "%SCRIPT_DIR%packages" -r "%SCRIPT_DIR%standard_checker\requirements.txt"
    
    REM インストール完了フラグを作成
    echo. > "%SCRIPT_DIR%packages\installed.flag"
    echo ✅ 依存関係のインストールが完了しました
)

REM データディレクトリの作成
if not exist "%SCRIPT_DIR%standard_checker\data\input" mkdir "%SCRIPT_DIR%standard_checker\data\input"
if not exist "%SCRIPT_DIR%standard_checker\data\output" mkdir "%SCRIPT_DIR%standard_checker\data\output"
if not exist "%SCRIPT_DIR%standard_checker\data\logs" mkdir "%SCRIPT_DIR%standard_checker\data\logs"

REM アプリケーション起動
echo 🌐 アプリケーションを起動中...
echo.
echo 📋 使用方法:
echo 1. ブラウザで http://localhost:8000 にアクセス
echo 2. PDFファイルをアップロードして標準規格を抽出
echo 3. 停止するには Ctrl+C を押してください
echo.

cd /d "%SCRIPT_DIR%standard_checker"
"%PYTHON_PATH%" -m app.main

pause 