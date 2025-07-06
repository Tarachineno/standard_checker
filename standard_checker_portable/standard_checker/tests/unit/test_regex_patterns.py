"""
PDF解析パターンのテストクラス
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

class TestPDFParserPatterns:
    """PDF解析パターンのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.parser = PDFParser()
    
    @pytest.mark.parametrize("text,expected_type,expected_number", [
        ("EN 301 489-17:2017", "EN", "301 489-17"),
        ("ETSI EN 301 489-17:2017", "ETSI EN", "301 489-17"),
        ("IEC 62368-1:2014", "IEC", "62368-1"),
        ("ISO/IEC 17025:2017", "ISO/IEC", "17025"),
        ("ISO 9001:2015", "ISO", "9001"),
        ("CISPR 11:2015", "CISPR", "11"),
        ("EN 55032:2015", "EN", "55032"),
        ("IEC 61000-4-2:2008", "IEC", "61000-4-2"),
    ])
    def test_standard_patterns(self, text, expected_type, expected_number):
        """標準規格パターンのテスト"""
        result = self.parser._extract_from_text(text)
        
        assert len(result) >= 1
        
        # 期待される標準規格が抽出されているか確認
        found = False
        for standard in result:
            if (standard['type'] == expected_type and 
                expected_number in standard['number_part']):
                found = True
                break
        
        assert found, f"Expected {expected_type} {expected_number} not found in {result}"
    
    def test_complex_document(self):
        """複雑な文書からの抽出テスト"""
        complex_text = """
        SCOPE OF ACCREDITATION TO ISO/IEC 17025:2017
        
        This laboratory is accredited in accordance with the recognized International Standard ISO/IEC 17025:2017.
        
        The following standards are covered:
        - EN 301 489-1:2017 (EMC requirements for radio equipment)
        - EN 301 489-17:2017 (EMC requirements for broadband data transmission systems)
        - IEC 62368-1:2014 (Audio/video information and communication technology equipment)
        - EN 55032:2015/AC:2016 (EMC requirements for multimedia equipment)
        - EN 55035:2017 (EMC requirements for multimedia equipment - Immunity requirements)
        - CISPR 11:2015+A1:2016 (Industrial, scientific and medical equipment)
        
        Additional directives:
        RED 2014/53/EU, LVD 2014/35/EU, EMC 2014/30/EU
        """
        
        result = self.parser._extract_from_text(complex_text)
        
        # 期待される標準規格数
        assert len(result) >= 6
        
        # 各標準規格の確認
        extracted_numbers = [s['number_part'] for s in result]
        expected_numbers = ['17025', '301 489-1', '301 489-17', '62368-1', '55032', '55035', '11']
        
        for expected in expected_numbers:
            assert any(expected in num for num in extracted_numbers), f"Expected {expected} not found"
    
    def test_malformed_standards(self):
        """形式が不正な標準規格のテスト"""
        malformed_text = """
        EN301489-17:2017  (スペースなし)
        EN 301489-17      (年度なし)
        EN 301 489 17:2017 (余分なスペース)
        EN-301-489-17:2017 (ハイフン区切り)
        """
        
        result = self.parser._extract_from_text(malformed_text)
        
        # 一部は抽出されるはず
        assert len(result) >= 1
    
    def test_japanese_document(self):
        """日本語文書からの抽出テスト"""
        japanese_text = """
        認定範囲：ISO/IEC 17025:2017
        
        適用規格：
        ・EN 301 489-17:2017（無線機器のEMC要求事項）
        ・IEC 62368-1:2014（AV・ICT機器の安全要求事項）
        ・JIS C 6950-1:2016（情報技術機器の安全性）
        
        備考：上記規格に基づく試験を実施する。
        """
        
        result = self.parser._extract_from_text(japanese_text)
        
        assert len(result) >= 3
        
        # 抽出された標準規格の確認
        types = [s['type'] for s in result]
        assert 'ISO/IEC' in types
        assert 'EN' in types
        assert 'IEC' in types
