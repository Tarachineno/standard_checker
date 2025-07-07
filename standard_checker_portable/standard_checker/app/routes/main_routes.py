"""
メインルート - Web UI用のルート
"""

from fastapi import APIRouter, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys
from modules.pdf_parser.parser import PDFParser
from modules.standards.registry import StandardRegistry
from modules.etsi_crawler.query import ETSICrawler

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse) 
async def upload_page(request: Request):
    """アップロードページ"""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """PDFファイルのアップロード処理"""
    try:
        # ファイル保存
        file_path = Path(f"data/input/{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # PDF解析
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(file_path)
        
        # 標準レジストリに登録
        registry = StandardRegistry()
        for standard in standards:
            registry.add_standard(standard)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "standards": standards,
            "filename": file.filename
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """結果表示ページ"""
    registry = StandardRegistry()
    standards = registry.get_all_standards()
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "standards": standards
    })

@router.get("/etsi_check", response_class=HTMLResponse)
async def etsi_check_page(request: Request):
    """ETSI確認ページ"""
    return templates.TemplateResponse("etsi_check.html", {"request": request})

@router.post("/etsi_check")
async def etsi_check_process(request: Request, standard_number: str = Form(...)):
    """ETSI確認処理"""
    try:
        crawler = ETSICrawler()
        etsi_info = crawler.search_standard(standard_number)
        
        return templates.TemplateResponse("etsi_results.html", {
            "request": request,
            "standard_number": standard_number,
            "etsi_info": etsi_info
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })