@echo off
setlocal enabledelayedexpansion

echo 🚀 Standard Version Checker セットアップ開始...

REM 色付きの出力関数
call :print_success "セットアップスクリプトを開始します"

REM Pythonのバージョンチェック
echo ℹ️  Pythonのバージョンを確認中...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません。Python 3.8以上をインストールしてください。
    pause
    exit /b 1
)

REM 仮想環境の作成
echo ℹ️  仮想環境を作成中...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ 仮想環境が作成されました
) else (
    echo ℹ️  仮想環境は既に存在します
)

REM 仮想環境のアクティベート
echo ℹ️  仮想環境をアクティベート中...
call .venv\Scripts\activate.bat
echo ✅ 仮想環境がアクティベートされました

REM pipのアップグレード
echo ℹ️  pipを最新版にアップグレード中...
python -m pip install --upgrade pip

REM 依存関係のインストール
echo ℹ️  依存関係をインストール中...
pip install -r requirements.txt
echo ✅ 依存関係のインストールが完了しました

REM データディレクトリの作成
echo ℹ️  データディレクトリを作成中...
if not exist "data\input" mkdir data\input
if not exist "data\output" mkdir data\output
if not exist "data\logs" mkdir data\logs
echo ✅ データディレクトリが作成されました

REM 環境設定ファイルの確認
if not exist ".env" (
    if exist ".env.example" (
        echo ℹ️  環境設定ファイルをコピー中...
        copy .env.example .env >nul
        echo ✅ 環境設定ファイルが作成されました
        echo ⚠️  .envファイルを必要に応じて編集してください
    ) else (
        echo ℹ️  環境設定ファイルは不要です
    )
) else (
    echo ℹ️  環境設定ファイルは既に存在します
)

REM テストの実行
echo ℹ️  テストを実行中...
python -m pytest tests/unit/ -v --tb=short
if errorlevel 1 (
    echo ⚠️  テストでエラーが発生しましたが、セットアップは続行します
) else (
    echo ✅ テストが成功しました
)

echo.
echo 🎉 セットアップが完了しました！
echo.
echo 📋 次のステップ:
echo 1. アプリケーションを起動:
echo    cd standard_checker
echo    python -m app.main
echo.
echo 2. ブラウザでアクセス:
echo    http://localhost:8000
echo.
echo 📖 詳細な使用方法は README.md を参照してください
echo.
pause
exit /b 0

:print_success
echo ✅ %~1
goto :eof 