# Standerd_Version_Checker

ISO/IEC 17025のスコープ認定証明書から支援標準を抽出し、ETSIのWEBポータルと連携して最新状況を確認するWEBアプリケーション。

## 機能

- PDFから標準規格の抽出
- ETSIポータルとの連携による最新状況確認
- フィルタリング機能
- Web UI / CLI両対応

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境設定
cp .env.example .env
# .envファイルを編集して設定を調整

# アプリケーション起動
cd standard_checker
python app/main.py
```

## 使い方

### Web UI
1. ブラウザで http://localhost:8000 にアクセス
2. PDFファイルをアップロード
3. 抽出された標準規格の一覧を確認
4. 必要に応じてフィルタリング

### CLI
```bash
# 全体パイプライン実行
python scripts/run_pipeline.py --input data/input/scope.pdf

# ETSI更新状況のみ確認
python scripts/update_check.py
```

## テスト

```bash
# 単体テスト
pytest tests/unit/

# 結合テスト
pytest tests/integration/

# 全テスト
pytest
```

## プロジェクト構造

```
standard_checker/
├── app/                  # WEBアプリ本体
│   ├── main.py          # FastAPI エントリー
│   ├── routes/          # ルート分割
│   └── templates/       # UI (Jinja2)
├── modules/             # ビジネスロジック
│   ├── pdf_parser/      # PDF解析
│   ├── standards/       # Standardモデル管理
│   ├── etsi_crawler/    # ETSIポータルクローラー
│   └── filter/          # 条件フィルター
├── data/                # データ格納
│   ├── input/           # PDFや入力データ
│   ├── output/          # 抽出結果
│   └── logs/            # ログ
├── tests/               # テスト
├── scripts/             # 自動化スクリプト
└── requirements.txt     # 依存パッケージ
```

## 今後の拡張予定

- JSA / IEC / IEEE など他標準化団体との連携
- NANDO や EUOJとの連携
- メール通知機能
- GitHub Actions による自動検出ジョブ