"""
Standard_Version_Checker - FastAPI メインアプリケーション
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数読み込み
load_dotenv()

# データディレクトリ作成
def create_directories():
    """必要なディレクトリを作成"""
    directories = [
        "data/input",
        "data/output", 
        "data/logs"
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    import psutil
    import signal
    # 起動時
    create_directories()
    print("Standard_Version_Checker が起動しました")
    yield
    # シャットダウン時
    try:
        # ChromeDriverプロセスを終了
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chromedriver' in proc.info['name'].lower():
                try:
                    os.kill(proc.info['pid'], signal.SIGTERM)
                except:
                    pass
        # 一時ディレクトリのクリーンアップ
        import tempfile
        import shutil
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('tmp'):
                try:
                    path = os.path.join(temp_dir, item)
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except:
                    pass
    except Exception as e:
        print(f"クリーンアップ中にエラーが発生: {e}")
    print("Standard_Version_Checker がシャットダウンしました")

# アプリケーション初期化
app = FastAPI(
    title="Standard Version Checker",
    description="ISO/IEC 17025スコープ認定証明書から支援標準を抽出し、ETSIポータルと連携",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# テンプレートとスタティックファイル設定
templates = Jinja2Templates(directory="templates")

# ルート設定
from app.routes import main_routes, api_routes

app.include_router(main_routes.router)
app.include_router(api_routes.router, prefix="/api")

@app.get("/")
async def root(request: Request):
    """ルートページ"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "message": "Standard_Version_Checker is running"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )