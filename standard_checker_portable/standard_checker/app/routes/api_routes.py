"""
API ルート - REST API用のルート
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import sys
from typing import List, Dict, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.pdf_parser.parser import PDFParser
from modules.standards.registry import StandardRegistry
from modules.etsi_crawler.query import ETSICrawler
from modules.filter.filter import StandardFilter

router = APIRouter()

@router.post("/extract")
async def extract_standards(file: UploadFile = File(...)):
    """PDFから標準規格を抽出"""
    try:
        # ファイル保存
        file_path = Path(f"data/input/{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # PDF解析
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(file_path)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "standards_count": len(standards),
            "standards": standards
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standards")
async def get_standards():
    """登録された標準規格一覧を取得"""
    try:
        registry = StandardRegistry()
        standards = registry.get_all_standards()
        
        return JSONResponse(content={
            "status": "success",
            "count": len(standards),
            "standards": standards
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/etsi/{standard_number}")
async def get_etsi_info(standard_number: str):
    """指定された標準規格のETSI情報を取得"""
    try:
        with ETSICrawler() as crawler:
            etsi_info = crawler.search_standard(standard_number)
            return JSONResponse(content={
                "status": "success",
                "standard_number": standard_number,
                "etsi_info": etsi_info
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter")
async def filter_standards(
    status: Optional[str] = None,
    directive: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
):
    """標準規格をフィルタリング"""
    try:
        registry = StandardRegistry()
        all_standards = registry.get_all_standards()
        
        filter_obj = StandardFilter()
        filtered_standards = filter_obj.apply_filters(
            all_standards,
            status=status,
            directive=directive,
            date_start=date_start,
            date_end=date_end
        )
        
        return JSONResponse(content={
            "status": "success",
            "total_count": len(all_standards),
            "filtered_count": len(filtered_standards),
            "standards": filtered_standards
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/standards/{standard_id}")
async def delete_standard(standard_id: str):
    """標準規格を削除"""
    try:
        registry = StandardRegistry()
        success = registry.remove_standard(standard_id)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": f"Standard {standard_id} deleted successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Standard not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{format}")
async def export_standards(format: str):
    """標準規格データをエクスポート"""
    try:
        registry = StandardRegistry()
        standards = registry.get_all_standards()
        
        if format.lower() == "csv":
            # CSV形式でエクスポート
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["number", "version", "status", "directive"])
            writer.writeheader()
            for standard in standards:
                writer.writerow(standard)
            
            return JSONResponse(content={
                "status": "success",
                "format": "csv",
                "data": output.getvalue()
            })
        
        elif format.lower() == "json":
            return JSONResponse(content={
                "status": "success",
                "format": "json",
                "data": standards
            })
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))