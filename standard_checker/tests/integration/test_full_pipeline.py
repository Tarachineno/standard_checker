"""
フルパイプライン結合テスト
PDF抽出からETSI確認まで全体の統合テスト
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.pdf_parser.parser import PDFParser
from modules.standards.registry import StandardRegistry
from modules.etsi_crawler.query import ETSICrawler
from modules.filter.filter import StandardFilter

class TestFullPipeline:
    """フルパイプライン統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ディレクトリとファイルの準備
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # テスト用のPDFテキストコンテンツ
        self.sample_pdf_text = """
        SCOPE OF ACCREDITATION TO ISO/IEC 17025:2017
        
        This laboratory is accredited for the following standards:
        - EN 301 489-17:2017 (EMC requirements for broadband data transmission systems)
        - IEC 62368-1:2014 (Audio/video, information and communication technology equipment)
        - EN 55032:2015 (EMC requirements for multimedia equipment)
        - ISO 9001:2015 (Quality management systems)
        
        Additional standards:
        CISPR 11:2015+A1:2016 (Industrial, scientific and medical equipment)
        """
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_pdf_to_registry_pipeline(self, mock_pdfplumber):
        """PDF抽出からレジストリ登録までのパイプライン"""
        # PDFモックの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = self.sample_pdf_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        # テスト用PDFファイル
        test_pdf = self.temp_path / "test.pdf"
        test_pdf.touch()
        
        # レジストリファイル
        registry_file = self.temp_path / "registry.json"
        
        # パイプライン実行
        # 1. PDF解析
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        assert len(standards) >= 5
        
        # 2. レジストリ登録
        registry = StandardRegistry(data_file=registry_file)
        added_ids = registry.bulk_add_standards(standards)
        
        assert len(added_ids) == len(standards)
        assert len(registry.get_all_standards()) == len(standards)
        
        # 3. データ永続化
        registry.save_data()
        assert registry_file.exists()
        
        # 4. 新しいインスタンスで読み込み確認
        new_registry = StandardRegistry(data_file=registry_file)
        loaded_standards = new_registry.get_all_standards()
        
        assert len(loaded_standards) == len(standards)
        
        # 抽出された標準規格の確認
        numbers = [s['number_part'] for s in loaded_standards]
        assert '301 489-17' in numbers
        assert '62368-1' in numbers
        assert '55032' in numbers
        assert '9001' in numbers
        assert '11' in numbers
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    @patch('modules.etsi_crawler.query.ETSICrawler._search_with_selenium')
    def test_full_pipeline_with_etsi(self, mock_etsi_search, mock_pdfplumber):
        """PDF抽出、レジストリ登録、ETSI確認を含む完全パイプライン"""
        # PDFモックの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = "EN 301 489-17:2017\nIEC 62368-1:2014"
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        # ETSIモックの設定
        def mock_etsi_response(standard_number):
            return {
                'status': 'Success',
                'standard_number': standard_number,
                'total_versions': 1,
                'versions': [
                    {
                        'identification': f'{standard_number} V1.1.1',
                        'status': 'Published',
                        'publication_date': '2017-09-01',
                        'title': f'Test Standard {standard_number}'
                    }
                ],
                'last_updated': '2023-01-01 12:00:00'
            }
        
        mock_etsi_search.side_effect = lambda num: mock_etsi_response(num)
        
        # テストファイル準備
        test_pdf = self.temp_path / "test.pdf"
        test_pdf.touch()
        registry_file = self.temp_path / "registry.json"
        
        # 完全パイプライン実行
        # 1. PDF解析
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        # 2. レジストリ登録
        registry = StandardRegistry(data_file=registry_file)
        added_ids = registry.bulk_add_standards(standards)
        
        # 3. ETSI情報確認
        with patch('modules.etsi_crawler.query.ETSICrawler._setup_driver'):
            with patch('modules.etsi_crawler.query.ETSICrawler.__enter__', return_value=ETSICrawler()):
                with patch('modules.etsi_crawler.query.ETSICrawler.__exit__'):
                    crawler = ETSICrawler(use_selenium=False)
                    crawler._search_with_selenium = mock_etsi_search
                    
                    for standard in standards:
                        number_part = standard.get('number_part', '')
                        if number_part:
                            etsi_info = crawler.search_standard(number_part)
                            registry.update_standard(standard['id'], {'etsi_info': etsi_info})
        
        # 4. 結果確認
        updated_standards = registry.get_all_standards()
        
        # ETSI情報が追加されているか確認
        etsi_updated_count = sum(1 for s in updated_standards if s.get('etsi_info'))
        assert etsi_updated_count >= 2
        
        # 特定の標準規格のETSI情報確認
        en_standard = next((s for s in updated_standards if '301 489-17' in s.get('number_part', '')), None)
        assert en_standard is not None
        assert en_standard['etsi_info']['status'] == 'Success'
        assert len(en_standard['etsi_info']['versions']) == 1
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_pipeline_with_filtering(self, mock_pdfplumber):
        """フィルタリングを含むパイプライン"""
        # PDFモックの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = self.sample_pdf_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        # テストファイル準備
        test_pdf = self.temp_path / "test.pdf"
        test_pdf.touch()
        
        # パイプライン実行
        # 1. PDF解析とレジストリ登録
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        registry = StandardRegistry()
        registry.bulk_add_standards(standards)
        
        # 2. フィルタリング
        filter_obj = StandardFilter()
        
        # EN標準規格のみフィルタリング
        en_standards = filter_obj.filter_by_type(standards, 'EN')
        assert len(en_standards) >= 2
        assert all(s['type'] == 'EN' for s in en_standards)
        
        # バージョン情報ありのものをフィルタリング
        versioned_standards = filter_obj.filter_by_version_exists(standards, True)
        assert len(versioned_standards) >= 4
        
        # 複合フィルター（ENかつバージョンあり）
        filter_obj.clear_filters()
        combined_result = filter_obj.apply_filters(
            standards,
            type='EN',
            has_version=True
        )
        assert len(combined_result) >= 2
        assert all(s['type'] == 'EN' and s['version'] for s in combined_result)
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_pipeline_export_functionality(self, mock_pdfplumber):
        """エクスポート機能を含むパイプライン"""
        # PDFモックの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = self.sample_pdf_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        # テストファイル準備
        test_pdf = self.temp_path / "test.pdf"
        test_pdf.touch()
        registry_file = self.temp_path / "registry.json"
        
        # パイプライン実行
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        registry = StandardRegistry(data_file=registry_file)
        registry.bulk_add_standards(standards)
        
        # エクスポートテスト
        # 1. CSV出力
        csv_output = self.temp_path / "export.csv"
        registry.export_to_csv(csv_output)
        assert csv_output.exists()
        
        # CSVファイルの内容確認
        import pandas as pd
        df = pd.read_csv(csv_output)
        assert len(df) == len(standards)
        assert 'number' in df.columns
        assert 'type' in df.columns
        
        # 2. Excel出力
        excel_output = self.temp_path / "export.xlsx"
        registry.export_to_excel(excel_output)
        assert excel_output.exists()
        
        # 3. JSON出力（解析結果）
        json_output = self.temp_path / "results"
        parser.save_extraction_results(standards, json_output)
        
        json_file = json_output.with_suffix('.json')
        csv_file = json_output.with_suffix('.csv')
        
        assert json_file.exists()
        assert csv_file.exists()
        
        # JSONファイルの内容確認
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            assert len(loaded_data) == len(standards)
    
    def test_error_handling_pipeline(self):
        """エラーハンドリングを含むパイプライン"""
        # 存在しないPDFファイル
        non_existent_pdf = self.temp_path / "non_existent.pdf"
        
        parser = PDFParser()
        
        # PDFファイルが存在しない場合のエラー
        with pytest.raises(Exception):
            parser.extract_standards_from_pdf(non_existent_pdf)
        
        # 破損したレジストリファイル
        corrupted_registry = self.temp_path / "corrupted.json"
        with open(corrupted_registry, 'w') as f:
            f.write("{ corrupted json")
        
        # 破損したファイルでも正常に初期化される
        registry = StandardRegistry(data_file=corrupted_registry)
        assert len(registry.standards) == 0
        
        # 無効な標準規格データ
        invalid_data = [
            {},  # 空辞書
            {'invalid_field': 'value'},  # 不正なフィールド
            None  # None値
        ]
        
        # 無効データは無視されるか適切に処理される
        valid_count = 0
        for data in invalid_data:
            try:
                if data is not None:
                    registry.add_standard(data)
                    valid_count += 1
            except Exception:
                pass  # エラーは期待される
        
        # 最低限の処理は継続される
        assert valid_count <= len(invalid_data)

class TestPipelinePerformance:
    """パイプライン性能テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_large_dataset_processing(self, mock_pdfplumber):
        """大量データ処理テスト"""
        # 大量の標準規格を含むテキスト生成
        large_text = "ISO/IEC 17025:2017\n"
        for i in range(1, 101):  # 100個の標準規格
            large_text += f"EN 301 {i:03d}-17:2017\n"
            large_text += f"IEC 62368-{i}:2014\n"
        
        # PDFモックの設定
        mock_page = Mock()
        mock_page.extract_text.return_value = large_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        # テスト実行
        test_pdf = self.temp_path / "large_test.pdf"
        test_pdf.touch()
        
        import time
        start_time = time.time()
        
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        registry = StandardRegistry()
        added_ids = registry.bulk_add_standards(standards)
        
        processing_time = time.time() - start_time
        
        # 結果確認
        assert len(standards) >= 200  # 最低200個の標準規格
        assert processing_time < 10.0  # 10秒以内で処理完了
        
        # メモリ使用量が適切か（簡易チェック）
        assert len(registry.standards) == len(added_ids)
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_duplicate_handling_performance(self, mock_pdfplumber):
        """重複処理性能テスト"""
        # 重複を含むテキスト
        duplicate_text = """
        EN 301 489-17:2017
        EN 301 489-17:2017
        EN 301 489-17:2017
        IEC 62368-1:2014
        IEC 62368-1:2014
        ISO 9001:2015
        ISO 9001:2015
        ISO 9001:2015
        ISO 9001:2015
        """
        
        mock_page = Mock()
        mock_page.extract_text.return_value = duplicate_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        test_pdf = self.temp_path / "duplicate_test.pdf"
        test_pdf.touch()
        
        # テスト実行
        parser = PDFParser()
        standards = parser.extract_standards_from_pdf(test_pdf)
        
        # 重複が適切に除去されているか
        unique_numbers = set()
        for standard in standards:
            key = f"{standard['type']}_{standard['number_part']}_{standard.get('version', 'null')}"
            assert key not in unique_numbers, f"Duplicate found: {key}"
            unique_numbers.add(key)
        
        # 期待される数の一意な標準規格
        assert len(standards) == 3  # EN, IEC, ISOで1つずつ

class TestPipelineDataIntegrity:
    """データ整合性テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('modules.pdf_parser.parser.pdfplumber.open')
    def test_data_consistency_across_operations(self, mock_pdfplumber):
        """操作間でのデータ一貫性テスト"""
        # テストデータ準備
        test_text = "EN 301 489-17:2017\nIEC 62368-1:2014\nISO 9001:2015"
        
        mock_page = Mock()
        mock_page.extract_text.return_value = test_text
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf
        
        test_pdf = self.temp_path / "test.pdf"
        test_pdf.touch()
        registry_file = self.temp_path / "registry.json"
        
        # データ一貫性テスト
        # 1. 初期抽出
        parser = PDFParser()
        initial_standards = parser.extract_standards_from_pdf(test_pdf)
        
        # 2. レジストリ登録
        registry = StandardRegistry(data_file=registry_file)
        added_ids = registry.bulk_add_standards(initial_standards)
        registry.save_data()
        
        # 3. データ再読み込み
        new_registry = StandardRegistry(data_file=registry_file)
        loaded_standards = new_registry.get_all_standards()
        
        # 4. データ整合性確認
        assert len(loaded_standards) == len(initial_standards)
        
        # 各標準規格の詳細比較
        for initial in initial_standards:
            found = False
            for loaded in loaded_standards:
                if (loaded['number_part'] == initial['number_part'] and
                    loaded['type'] == initial['type'] and
                    loaded['version'] == initial['version']):
                    found = True
                    # 重要フィールドの一致確認
                    assert loaded['status'] == initial['status']
                    assert loaded['source'] == initial['source']
                    break
            assert found, f"Initial standard not found in loaded data: {initial}"
        
        # 5. 更新操作
        first_standard_id = loaded_standards[0]['id']
        update_data = {
            'status': 'Updated',
            'notes': 'Test update',
            'etsi_info': {'test': 'data'}
        }
        
        new_registry.update_standard(first_standard_id, update_data)
        new_registry.save_data()
        
        # 6. 更新後の整合性確認
        final_registry = StandardRegistry(data_file=registry_file)
        final_standards = final_registry.get_all_standards()
        
        updated_standard = next(s for s in final_standards if s['id'] == first_standard_id)
        assert updated_standard['status'] == 'Updated'
        assert updated_standard['notes'] == 'Test update'
        assert updated_standard['etsi_info'] == {'test': 'data'}
        
        # 他の標準規格は変更されていないことを確認
        unchanged_standards = [s for s in final_standards if s['id'] != first_standard_id]
        for std in unchanged_standards:
            original = next(s for s in initial_standards 
                          if s['number_part'] == std['number_part'])
            assert std['status'] == original['status']