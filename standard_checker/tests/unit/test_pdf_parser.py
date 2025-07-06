"""
PDF解析モジュールの単体テスト
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.pdf_parser.parser import PDFParser

class TestPDFParser:
    """PDFParserクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.parser = PDFParser()
    
    def test_init(self):
        """初期化テスト"""
        assert self.parser is not None
        assert len(self.parser.standard_patterns) > 0
    
    def test_parse_standard_match_en_standard(self):
        """EN標準規格の解析テスト"""
        import re
        
        pattern = r'EN\s+(\d+(?:-\d+)*):?(\d{4})?'
        text = "EN 301 489-17:2017"
        match = re.search(pattern, text)
        
        result = self.parser._parse_standard_match(match, pattern)
        
        assert result is not None
        assert result['type'] == 'EN'
        assert result['number_part'] == '301 489-17'
        assert result['version'] == '2017'
        assert 'EN 301 489-17:2017' in result['number']
    
    def test_parse_standard_match_iso_iec_standard(self):
        """ISO/IEC標準規格の解析テスト"""
        import re
        
        pattern = r'ISO/IEC\s+(\d+(?:-\d+)*):?(\d{4})?'
        text = "ISO/IEC 17025:2017"
        match = re.search(pattern, text)
        
        result = self.parser._parse_standard_match(match, pattern)
        
        assert result is not None
        assert result['type'] == 'ISO/IEC'
        assert result['number_part'] == '17025'
        assert result['version'] == '2017'
    
    def test_parse_standard_match_without_year(self):
        """年度なしの標準規格解析テスト"""
        import re
        
        pattern = r'EN\s+(\d+(?:-\d+)*):?(\d{4})?'
        text = "EN 301 489-17"
        match = re.search(pattern, text)
        
        result = self.parser._parse_standard_match(match, pattern)
        
        assert result is not None
        assert result['version'] is None
        assert result['number_part'] == '301 489-17'
    
    def test_extract_from_text(self):
        """テキストからの抽出テスト"""
        test_text = """
        This document covers the following standards:
        EN 301 489-17:2017
        IEC 62368-1:2014
        ISO 9001:2015
        CISPR 11:2015
        """
        
        result = self.parser._extract_from_text(test_text)
        
        assert len(result) >= 4
        
        # EN標準規格の確認
        en_standards = [s for s in result if s['type'] == 'EN']
        assert len(en_standards) >= 1
        assert any('301 489-17' in s['number_part'] for s in en_standards)
        
        # IEC標準規格の確認
        iec_standards = [s for s in result if s['type'] == 'IEC']
        assert len(iec_standards) >= 1
        assert any('62368-1' in s['number_part'] for s in iec_standards)
    
    def test_remove_duplicates(self):
        """重複除去テスト"""
        standards = [
            {
                'type': 'EN',
                'number_part': '301 489-17',
                'version': '2017',
                'id': 'test1'
            },
            {
                'type': 'EN',
                'number_part': '301 489-17',
                'version': '2017',
                'id': 'test2'
            },
            {
                'type': 'EN',
                'number_part': '301 489-17',
                'version': '2018',
                'id': 'test3'
            }
        ]
        
        result = self.parser._remove_duplicates(standards)
        
        # 同じ標準規格の異なるバージョンは別として扱う
        assert len(result) == 2
        
        # 同じ標準規格・同じバージョンは1つだけ
        en_2017_count = sum(1 for s in result 
                           if s['type'] == 'EN' and s['number_part'] == '301 489-17' and s['version'] == '2017')
        assert en_2017_count == 1
    
    def test_enrich_from_table_row(self):
        """テーブル行からの情報抽出テスト"""
        standard = {
            'type': 'EN',
            'number_part': '301 489-17',
            'version': '2017',
            'status': 'Active'
        }
        
        # ステータス情報を含む行
        row_with_status = ['EN 301 489-17:2017', 'Current', 'RED 2014/53/EU', 'Test Standard']
        result = self.parser._enrich_from_table_row(standard, row_with_status)
        
        assert result['status'] == 'Current'
        
        # 指令情報を含む行
        row_with_directive = ['EN 301 489-17:2017', 'Active', 'LVD 2014/35/EU', 'Test Standard']
        result = self.parser._enrich_from_table_row(standard, row_with_directive)
        
        assert 'LVD' in result.get('directive', '')
    
    @patch('pdfplumber.open')
    def test_extract_standards_from_pdf_success(self, mock_pdfplumber):
        """PDF抽出成功テスト"""
        # モックPDFオブジェクトの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = "EN 301 489-17:2017\nIEC 62368-1:2014"
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # テスト実行
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            result = self.parser.extract_standards_from_pdf(Path(tmp_file.name))
        
        assert len(result) >= 2
        assert any('301 489-17' in s['number_part'] for s in result)
        assert any('62368-1' in s['number_part'] for s in result)
    
    @patch('pdfplumber.open')
    def test_extract_standards_from_pdf_error(self, mock_pdfplumber):
        """PDF抽出エラーテスト"""
        mock_pdfplumber.side_effect = Exception("PDF読み込みエラー")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            with pytest.raises(Exception) as exc_info:
                self.parser.extract_standards_from_pdf(Path(tmp_file.name))
            
            assert "PDF読み込みエラー" in str(exc_info.value)
    
    def test_extract_from_tables(self):
        """テーブルデータからの抽出テスト"""
        table_data = [
            ['Standard', 'Version', 'Status'],
            ['EN 301 489-17:2017', '2017', 'Current'],
            ['IEC 62368-1:2014', '2014', 'Active'],
            ['', '', ''],  # 空行
            [None, None, None]  # None行
        ]
        
        result = self.parser._extract_from_tables(table_data)
        
        assert len(result) >= 2
        
        # 抽出された標準規格の確認
        standard_numbers = [s['number_part'] for s in result]
        assert '301 489-17' in standard_numbers
        assert '62368-1' in standard_numbers
    
    def test_save_extraction_results(self):
        """抽出結果保存テスト"""
        standards = [
            {
                'type': 'EN',
                'number': 'EN 301 489-17:2017',
                'number_part': '301 489-17',
                'version': '2017',
                'status': 'Active'
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_results"
            self.parser.save_extraction_results(standards, output_path)
            
            # CSVファイルの確認
            csv_path = output_path.with_suffix('.csv')
            assert csv_path.exists()
            
            # JSONファイルの確認
            json_path = output_path.with_suffix('.json')
            assert json_path.exists()
            
            # JSONファイルの内容確認
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                assert len(loaded_data) == 1
                assert loaded_data[0]['type'] == 'EN'

