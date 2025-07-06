#!/bin/bash

# Standard Version Checker 起動スクリプト

set -e

echo "🚀 Standard Version Checker を起動中..."

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

# 仮想環境の確認
if [ ! -d ".venv" ]; then
    print_warning "仮想環境が見つかりません。setup.shを実行してください。"
    exit 1
fi

# 仮想環境のアクティベート
print_info "仮想環境をアクティベート中..."
source .venv/bin/activate
print_success "仮想環境がアクティベートされました"

# アプリケーションの起動
print_info "アプリケーションを起動中..."
echo ""
echo "🌐 ブラウザで http://localhost:8000 にアクセスしてください"
echo "🛑 停止するには Ctrl+C を押してください"
echo ""

cd standard_checker
python -m app.main 