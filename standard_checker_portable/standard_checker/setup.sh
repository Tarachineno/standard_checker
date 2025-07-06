#!/bin/bash

# Standard Version Checker セットアップスクリプト
# このスクリプトは、Standard Version Checkerを簡単にセットアップします

set -e

echo "🚀 Standard Version Checker セットアップ開始..."

# 色付きの出力関数
print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[34mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

# Pythonのバージョンチェック
print_info "Pythonのバージョンを確認中..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_success "Python $python_version が検出されました（要件: $required_version以上）"
else
    print_error "Python $required_version以上が必要です。現在のバージョン: $python_version"
    exit 1
fi

# 仮想環境の作成
print_info "仮想環境を作成中..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "仮想環境が作成されました"
else
    print_info "仮想環境は既に存在します"
fi

# 仮想環境のアクティベート
print_info "仮想環境をアクティベート中..."
source .venv/bin/activate
print_success "仮想環境がアクティベートされました"

# pipのアップグレード
print_info "pipを最新版にアップグレード中..."
pip install --upgrade pip

# 依存関係のインストール
print_info "依存関係をインストール中..."
pip install -r requirements.txt
print_success "依存関係のインストールが完了しました"

# データディレクトリの作成
print_info "データディレクトリを作成中..."
mkdir -p data/input data/output data/logs
print_success "データディレクトリが作成されました"

# 環境設定ファイルの確認
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "環境設定ファイルをコピー中..."
        cp .env.example .env
        print_success "環境設定ファイルが作成されました"
        print_warning ".envファイルを必要に応じて編集してください"
    else
        print_info "環境設定ファイルは不要です"
    fi
else
    print_info "環境設定ファイルは既に存在します"
fi

# テストの実行
print_info "テストを実行中..."
if python -m pytest tests/unit/ -v --tb=short; then
    print_success "テストが成功しました"
else
    print_warning "テストでエラーが発生しましたが、セットアップは続行します"
fi

echo ""
print_success "🎉 セットアップが完了しました！"
echo ""
echo "📋 次のステップ:"
echo "1. アプリケーションを起動:"
echo "   cd standard_checker"
echo "   python -m app.main"
echo ""
echo "2. ブラウザでアクセス:"
echo "   http://localhost:8000"
echo ""
echo "📖 詳細な使用方法は README.md を参照してください"
echo "" 