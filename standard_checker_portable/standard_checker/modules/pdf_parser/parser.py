"""
PDF解析モジュール
ISO/IEC 17025認定証明書から標準規格を抽出する
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pdfplumber
import pandas as pd
from datetime import datetime

class PDFParser:
    """PDF解析クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.standard_patterns = [
            r'(?:ETSI\s+)?EN\s+([\d\s.-]+)(?::(\d{4}))?',  # EN 301 489-17:2017 or ETSI EN 301 489-17:2017
            r'IEC\s+([\d.-]+)(?::(\d{4}))?',  # IEC 62368-1:2014
            r'ISO(?:/IEC)?\s+([\d.-]+)(?::(\d{4}))?',  # ISO 9001:2015 or ISO/IEC 17025:2017
            r'CISPR\s+([\d.-]+)(?::(\d{4}))?',  # CISPR 11:2015
        ]
    
    def extract_standards_from_pdf(self, file_path: Path) -> List[Dict]:
        """
        PDFファイルから標準規格を抽出
        
        Args:
            file_path: PDFファイルのパス
            
        Returns:
            抽出された標準規格のリスト
        """
        try:
            standards = []
            
            with pdfplumber.open(file_path) as pdf:
                # 全ページのテキストを抽出
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # テーブルデータも抽出
                table_data = self._extract_table_data(pdf)
                
                # テキストベースの抽出
                text_standards = self._extract_from_text(full_text)
                standards.extend(text_standards)
                
                # テーブルベースの抽出
                table_standards = self._extract_from_tables(table_data)
                standards.extend(table_standards)
                
                # 重複除去
                standards = self._remove_duplicates(standards)
                
                # 抽出結果をログに記録
                self.logger.info(f"PDFから{len(standards)}件の標準規格を抽出しました")
                
                return standards
                
        except Exception as e:
            self.logger.error(f"PDF解析エラー: {str(e)}")
            raise
    
    def _extract_table_data(self, pdf) -> List[List]:
        """PDFからテーブルデータを抽出"""
        table_data = []
        
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_data.extend(table)
        
        return table_data
    
    def _extract_from_text(self, text: str) -> List[Dict]:
        """テキストから標準規格を抽出"""
        standards = []
        
        for pattern in self.standard_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                standard = self._parse_standard_match(match, pattern)
                if standard:
                    standards.append(standard)
        
        return standards
    
    def _extract_from_tables(self, table_data: List[List]) -> List[Dict]:
        """テーブルデータから標準規格を抽出"""
        standards = []
        
        for row in table_data:
            if not row:
                continue
                
            # 各セルを検査
            for cell in row:
                if not cell:
                    continue
                    
                for pattern in self.standard_patterns:
                    matches = re.finditer(pattern, str(cell), re.IGNORECASE)
                    for match in matches:
                        standard = self._parse_standard_match(match, pattern)
                        if standard:
                            # テーブルの他のセルから追加情報を取得
                            standard = self._enrich_from_table_row(standard, row)
                            standards.append(standard)
        
        return standards
    
    def _parse_standard_match(self, match, pattern: str) -> Optional[Dict]:
        """正規表現のマッチから標準規格情報を解析"""
        try:
            full_match = match.group(0)
            
            # 標準規格番号の抽出
            if "ETSI EN" in full_match:
                standard_type = "ETSI EN"
            elif "EN" in full_match:
                standard_type = "EN"
            elif "ISO/IEC" in full_match:
                standard_type = "ISO/IEC"
            elif "IEC" in full_match:
                standard_type = "IEC"
            elif "ISO" in full_match:
                standard_type = "ISO"
            elif "CISPR" in full_match:
                standard_type = "CISPR"
            else:
                standard_type = "Unknown"
            
            # 番号部分を抽出
            number_part = match.group(1).strip() if match.groups() else ""
            
            # 年度部分を抽出
            year_part = match.group(2) if len(match.groups()) >= 2 and match.group(2) else None
            
            # 標準規格番号を構築
            if number_part:
                standard_number = f"{standard_type} {number_part}"
                if year_part:
                    standard_number += f":{year_part}"
            else:
                standard_number = full_match
            
            return {
                "id": f"{standard_type}_{number_part}_{year_part or 'null'}",
                "number": standard_number,
                "type": standard_type,
                "number_part": number_part,
                "version": year_part,
                "status": "Active",  # デフォルト値
                "directive": None,
                "extracted_at": datetime.now().isoformat(),
                "source": "PDF"
            }
            
        except Exception as e:
            self.logger.warning(f"標準規格解析エラー: {str(e)}")
            return None
    
    def _enrich_from_table_row(self, standard: Dict, row: List) -> Dict:
        """テーブル行から追加情報を抽出"""
        # 状態情報を検索
        status_keywords = {
            "withdrawn": "Withdrawn",
            "superseded": "Superseded", 
            "current": "Current",
            "active": "Active",
            "published": "Published"
        }
        
        row_text = " ".join([str(cell) for cell in row if cell]).lower()
        
        for keyword, status in status_keywords.items():
            if keyword in row_text:
                standard["status"] = status
                break
        
        # 指令情報を検索
        directive_patterns = [
            r'RED\s+2014/53/EU',
            r'LVD\s+2014/35/EU',
            r'EMC\s+2014/30/EU',
            r'RoHS\s+2011/65/EU'
        ]
        
        for pattern in directive_patterns:
            if re.search(pattern, row_text, re.IGNORECASE):
                standard["directive"] = pattern
                break
        
        return standard
    
    def _remove_duplicates(self, standards: List[Dict]) -> List[Dict]:
        """重複する標準規格を除去"""
        seen = set()
        unique_standards = []
        
        for standard in standards:
            # 識別子を生成
            identifier = f"{standard['type']}_{standard['number_part']}_{standard.get('version', 'null')}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_standards.append(standard)
        
        return unique_standards
    
    def save_extraction_results(self, standards: List[Dict], output_path: Path):
        """抽出結果をファイルに保存"""
        try:
            # CSVとして保存
            df = pd.DataFrame(standards)
            csv_path = output_path.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            
            # JSONとして保存
            import json
            json_path = output_path.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(standards, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"抽出結果を保存しました: {csv_path}, {json_path}")
            
        except Exception as e:
            self.logger.error(f"結果保存エラー: {str(e)}")
            raise