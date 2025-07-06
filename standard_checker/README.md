# Standard Version Checker

ISO/IEC 17025のスコープ認定証明書から支援標準を抽出し、ETSIのWEBポータルと連携して最新状況を確認するWEBアプリケーション。

## 🚀 クイックスタート

### 前提条件
- Python 3.8以上
- Git

### 1. リポジトリのクローン
```bash
git clone https://github.com/Tarachineno/standard_checker.git
cd standard_checker
```

### 2. 仮想環境の作成とアクティベート
```bash
# 仮想環境を作成
python -m venv .venv

# 仮想環境をアクティベート
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. アプリケーションの起動
```bash
cd standard_checker
python -m app.main
```

### 5. ブラウザでアクセス
http://localhost:8000 にアクセスしてアプリケーションを使用開始！

## 📋 機能

- **PDF解析**: ISO/IEC 17025スコープ認定証明書から標準規格を自動抽出
- **ETSI連携**: ETSIポータルとの連携による最新状況確認
- **フィルタリング**: 抽出された標準規格の高度なフィルタリング機能
- **Web UI**: 直感的なWebインターフェース
- **CLI対応**: コマンドラインでの実行も可能
- **エクスポート**: 結果をCSV/Excel形式でエクスポート

## 🛠️ 詳細セットアップ

### 環境変数の設定（オプション）
```bash
# 環境設定ファイルをコピー
cp .env.example .env

# 必要に応じて.envファイルを編集
# デフォルト設定で動作するため、編集は任意です
```

### データディレクトリの確認
アプリケーション起動時に以下のディレクトリが自動作成されます：
- `data/input/` - PDFファイルのアップロード先
- `data/output/` - 抽出結果の保存先
- `data/logs/` - ログファイル

## 📖 使い方

### Web UI
1. ブラウザで http://localhost:8000 にアクセス
2. 「ファイルを選択」ボタンでPDFファイルをアップロード
3. 「アップロード」ボタンをクリック
4. 抽出された標準規格の一覧を確認
5. 必要に応じてフィルタリング機能を使用
6. 結果をCSV/Excel形式でエクスポート

### CLI（コマンドライン）
```bash
# 全体パイプライン実行
python scripts/run_pipeline.py --input data/input/scope.pdf

# ETSI更新状況のみ確認
python scripts/update_check.py

# ヘルプ表示
python scripts/run_pipeline.py --help
```

## 🧪 テスト

```bash
# 単体テスト
pytest tests/unit/

# 結合テスト
pytest tests/integration/

# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=modules --cov=app --cov-report=html
```

## 📁 プロジェクト構造

```
standard_checker/
├── app/                  # FastAPI Webアプリケーション
│   ├── main.py          # アプリケーションエントリーポイント
│   ├── routes/          # APIルート定義
│   │   ├── api_routes.py    # REST API
│   │   └── main_routes.py   # Webページ
│   └── templates/       # HTMLテンプレート（Jinja2）
├── modules/             # ビジネスロジック
│   ├── pdf_parser/      # PDF解析モジュール
│   ├── standards/       # 標準規格モデル管理
│   ├── etsi_crawler/    # ETSIポータルクローラー
│   └── filter/          # フィルタリング機能
├── data/                # データ格納ディレクトリ
│   ├── input/           # 入力PDFファイル
│   ├── output/          # 抽出結果
│   └── logs/            # ログファイル
├── tests/               # テストファイル
│   ├── unit/            # 単体テスト
│   └── integration/     # 結合テスト
├── scripts/             # ユーティリティスクリプト
├── requirements.txt     # Python依存関係
├── README.md           # このファイル
└── .gitignore          # Git除外設定
```

## 🔧 開発環境

### 開発用セットアップ
```bash
# 開発用依存関係をインストール
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# コードフォーマット
black standard_checker/

# リントチェック
flake8 standard_checker/
```

### デバッグモードでの起動
```bash
# デバッグモードで起動（自動リロード有効）
python -m app.main
```

## 🐛 トラブルシューティング

### よくある問題

**1. ポート8000が既に使用されている**
```bash
# 使用中のプロセスを確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>
```

**2. 仮想環境がアクティブになっていない**
```bash
# プロンプトに(.venv)が表示されているか確認
# 表示されていない場合は以下を実行
source .venv/bin/activate
```

**3. 依存関係のインストールエラー**
```bash
# pipを最新版に更新
pip install --upgrade pip

# キャッシュをクリアして再インストール
pip install --no-cache-dir -r requirements.txt
```

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題が発生した場合は、[GitHub Issues](https://github.com/Tarachineno/standard_checker/issues)で報告してください。

## 🔮 今後の拡張予定

- JSA / IEC / IEEE など他標準化団体との連携
- NANDO や EUOJとの連携
- メール通知機能
- GitHub Actions による自動検出ジョブ
- Docker対応
- データベース統合