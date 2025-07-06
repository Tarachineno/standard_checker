"""
標準規格レジストリの単体テスト
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.standards.registry import StandardEntry, StandardRegistry

class TestStandardEntry:
    """StandardEntryクラスのテスト"""
    
    def test_init_with_full_data(self):
        """完全なデータでの初期化テスト"""
        data = {
            'id': 'test-001',
            'number': 'EN 301 489-17:2017',
            'type': 'EN',
            'number_part': '301 489-17',
            'version': '2017',
            'status': 'Active',
            'directive': 'RED 2014/53/EU',
            'extracted_at': '2023-01-01T00:00:00',
            'source': 'PDF',
            'etsi_info': {'status': 'Published'},
            'notes': 'Test note'
        }
        
        entry = StandardEntry(data)
        
        assert entry.id == 'test-001'
        assert entry.number == 'EN 301 489-17:2017'
        assert entry.type == 'EN'
        assert entry.version == '2017'
        assert entry.status == 'Active'
        assert entry.etsi_info == {'status': 'Published'}
    
    def test_init_with_minimal_data(self):
        """最小限のデータでの初期化テスト"""
        data = {
            'number': 'EN 301 489-17:2017'
        }
        
        entry = StandardEntry(data)
        
        assert entry.id is not None  # 自動生成される
        assert entry.number == 'EN 301 489-17:2017'
        assert entry.type == ''
        assert entry.status == 'Unknown'
        assert entry.version is None
    
    def test_to_dict(self):
        """辞書変換テスト"""
        data = {
            'number': 'EN 301 489-17:2017',
            'type': 'EN',
            'status': 'Active'
        }
        
        entry = StandardEntry(data)
        result = entry.to_dict()
        
        assert isinstance(result, dict)
        assert result['number'] == 'EN 301 489-17:2017'
        assert result['type'] == 'EN'
        assert result['status'] == 'Active'
        assert 'id' in result
        assert 'extracted_at' in result
    
    def test_update_etsi_info(self):
        """ETSI情報更新テスト"""
        entry = StandardEntry({'number': 'EN 301 489-17:2017'})
        old_updated = entry.last_updated
        
        etsi_info = {
            'status': 'Published',
            'versions': [{'identification': 'V1.1.1', 'status': 'Current'}]
        }
        
        entry.update_etsi_info(etsi_info)
        
        assert entry.etsi_info == etsi_info
        assert entry.last_updated != old_updated
    
    def test_update_status(self):
        """ステータス更新テスト"""
        entry = StandardEntry({'number': 'EN 301 489-17:2017', 'status': 'Active'})
        old_updated = entry.last_updated
        
        entry.update_status('Withdrawn')
        
        assert entry.status == 'Withdrawn'
        assert entry.last_updated != old_updated

class TestStandardRegistry:
    """StandardRegistryクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ファイルを使用
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.registry = StandardRegistry(data_file=Path(self.temp_file.name))
        self.registry.standards.clear()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        Path(self.temp_file.name).unlink(missing_ok=True)
    
    def test_init_empty_registry(self):
        """空のレジストリ初期化テスト"""
        assert len(self.registry.standards) == 0
    
    def test_add_standard(self):
        """標準規格追加テスト"""
        standard_data = {
            'number': 'EN 301 489-17:2017',
            'type': 'EN',
            'number_part': '301 489-17',
            'version': '2017',
            'status': 'Active'
        }
        
        standard_id = self.registry.add_standard(standard_data)
        
        assert standard_id is not None
        assert len(self.registry.standards) == 1
        assert standard_id in self.registry.standards
        
        entry = self.registry.standards[standard_id]
        assert entry.number == 'EN 301 489-17:2017'
        assert entry.type == 'EN'
    
    def test_add_duplicate_standard(self):
        """重複標準規格追加テスト"""
        standard_data = {
            'number': 'EN 301 489-17:2017',
            'type': 'EN',
            'number_part': '301 489-17',
            'version': '2017'
        }
        
        # 1回目の追加
        id1 = self.registry.add_standard(standard_data)
        
        # 2回目の追加（重複）
        id2 = self.registry.add_standard(standard_data)
        
        # 同じIDが返される
        assert id1 == id2
        assert len(self.registry.standards) == 1
    
    def test_get_standard(self):
        """標準規格取得テスト"""
        standard_data = {
            'number': 'EN 301 489-17:2017',
            'type': 'EN'
        }
        
        standard_id = self.registry.add_standard(standard_data)
        retrieved = self.registry.get_standard(standard_id)
        
        assert retrieved is not None
        assert retrieved.number == 'EN 301 489-17:2017'
        
        # 存在しないIDの場合
        non_existent = self.registry.get_standard('non-existent-id')
        assert non_existent is None
    
    def test_get_all_standards(self):
        """全標準規格取得テスト"""
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC'},
            {'number': 'ISO 9001:2015', 'type': 'ISO'}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        all_standards = self.registry.get_all_standards()
        
        assert len(all_standards) == 3
        assert all(isinstance(s, dict) for s in all_standards)
        
        numbers = [s['number'] for s in all_standards]
        assert 'EN 301 489-17:2017' in numbers
        assert 'IEC 62368-1:2014' in numbers
        assert 'ISO 9001:2015' in numbers
    
    def test_remove_standard(self):
        """標準規格削除テスト"""
        standard_data = {'number': 'EN 301 489-17:2017', 'type': 'EN'}
        standard_id = self.registry.add_standard(standard_data)
        
        # 削除前の確認
        assert len(self.registry.standards) == 1
        
        # 削除実行
        result = self.registry.remove_standard(standard_id)
        
        assert result is True
        assert len(self.registry.standards) == 0
        assert standard_id not in self.registry.standards
        
        # 存在しないIDの削除
        result = self.registry.remove_standard('non-existent-id')
        assert result is False
    
    def test_update_standard(self):
        """標準規格更新テスト"""
        standard_data = {'number': 'EN 301 489-17:2017', 'status': 'Active'}
        standard_id = self.registry.add_standard(standard_data)
        
        update_data = {
            'status': 'Withdrawn',
            'notes': 'Updated note',
            'etsi_info': {'status': 'Superseded'}
        }
        
        result = self.registry.update_standard(standard_id, update_data)
        
        assert result is True
        
        updated_entry = self.registry.get_standard(standard_id)
        assert updated_entry.status == 'Withdrawn'
        assert updated_entry.notes == 'Updated note'
        assert updated_entry.etsi_info == {'status': 'Superseded'}
        
        # 存在しないIDの更新
        result = self.registry.update_standard('non-existent-id', update_data)
        assert result is False
    
    def test_search_standards(self):
        """標準規格検索テスト"""
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN', 'status': 'Active'},
            {'number': 'EN 301 489-1:2017', 'type': 'EN', 'status': 'Active'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC', 'status': 'Withdrawn'},
            {'number': 'ISO 9001:2015', 'type': 'ISO', 'status': 'Active'}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        # タイプで検索
        en_standards = self.registry.search_standards(type='EN')
        assert len(en_standards) == 2
        assert all(s['type'] == 'EN' for s in en_standards)
        
        # ステータスで検索
        active_standards = self.registry.search_standards(status='Active')
        assert len(active_standards) == 3
        assert all(s['status'] == 'Active' for s in active_standards)
        
        # 番号の部分一致で検索
        en301_standards = self.registry.search_standards(number='301 489')
        assert len(en301_standards) == 2
        assert all('301 489' in s['number'] for s in en301_standards)
    
    def test_get_statistics(self):
        """統計情報取得テスト"""
        standards_data = [
            {'type': 'EN', 'status': 'Active', 'source': 'PDF', 'version': '2017'},
            {'type': 'EN', 'status': 'Active', 'source': 'PDF', 'version': None},
            {'type': 'IEC', 'status': 'Withdrawn', 'source': 'Manual', 'version': '2014'},
            {'type': 'ISO', 'status': 'Active', 'source': 'PDF', 'version': '2015', 'etsi_info': {'status': 'Published'}}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        stats = self.registry.get_statistics()
        
        assert stats['total_count'] == 4
        assert stats['by_type']['EN'] == 2
        assert stats['by_type']['IEC'] == 1
        assert stats['by_type']['ISO'] == 1
        assert stats['by_status']['Active'] == 3
        assert stats['by_status']['Withdrawn'] == 1
        assert stats['by_source']['PDF'] == 3
        assert stats['by_source']['Manual'] == 1
        assert stats['with_etsi_info'] == 1
        assert stats['with_version'] == 3
    
    def test_bulk_add_standards(self):
        """一括追加テスト"""
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC'},
            {'number': 'ISO 9001:2015', 'type': 'ISO'}
        ]
        
        added_ids = self.registry.bulk_add_standards(standards_data)
        
        assert len(added_ids) == 3
        assert len(self.registry.standards) == 3
        assert all(id in self.registry.standards for id in added_ids)
    
    def test_save_and_load_data(self):
        """データ保存・読み込みテスト"""
        # データを追加
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN', 'status': 'Active'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC', 'status': 'Withdrawn'}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        # 保存
        self.registry.save_data()
        
        # 新しいレジストリインスタンスで読み込み
        new_registry = StandardRegistry(data_file=Path(self.temp_file.name))
        
        assert len(new_registry.standards) == 2
        
        all_standards = new_registry.get_all_standards()
        numbers = [s['number'] for s in all_standards]
        assert 'EN 301 489-17:2017' in numbers
        assert 'IEC 62368-1:2014' in numbers
    
    def test_export_to_csv(self):
        """CSV出力テスト"""
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC'}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'test_export.csv'
            self.registry.export_to_csv(csv_path)
            
            assert csv_path.exists()
            
            # CSVファイルの内容確認
            import pandas as pd
            df = pd.read_csv(csv_path)
            assert len(df) == 2
            assert 'number' in df.columns
            assert 'type' in df.columns
    
    def test_export_to_excel(self):
        """Excel出力テスト"""
        standards_data = [
            {'number': 'EN 301 489-17:2017', 'type': 'EN'},
            {'number': 'IEC 62368-1:2014', 'type': 'IEC'}
        ]
        
        for data in standards_data:
            self.registry.add_standard(data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            excel_path = Path(temp_dir) / 'test_export.xlsx'
            self.registry.export_to_excel(excel_path)
            
            assert excel_path.exists()
            
            # Excelファイルの内容確認
            import pandas as pd
            df = pd.read_excel(excel_path, sheet_name='Standards')
            assert len(df) == 2
            
            # 統計シートの確認
            stats_df = pd.read_excel(excel_path, sheet_name='Statistics')
            assert len(stats_df) > 0

class TestStandardRegistryEdgeCases:
    """StandardRegistryのエッジケーステスト"""
    
    def test_load_corrupted_data_file(self):
        """破損したデータファイルの読み込みテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write("{ corrupted json data")
            temp_file.flush()
            
            # 破損したファイルでも正常に初期化される
            registry = StandardRegistry(data_file=Path(temp_file.name))
            assert len(registry.standards) == 0
            
            Path(temp_file.name).unlink()
    
    def test_load_non_existent_data_file(self):
        """存在しないデータファイルの読み込みテスト"""
        non_existent_path = Path("/tmp/non_existent_file.json")
        registry = StandardRegistry(data_file=non_existent_path)
        
        assert len(registry.standards) == 0
    
    def test_add_standard_with_missing_fields(self):
        """フィールド不足の標準規格追加テスト"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            registry = StandardRegistry(data_file=Path(temp_file.name))
            
            # 最小限のデータ
            minimal_data = {'number': 'EN 123:2020'}
            standard_id = registry.add_standard(minimal_data)
            
            assert standard_id is not None
            entry = registry.get_standard(standard_id)
            assert entry.number == 'EN 123:2020'
            assert entry.type == ''  # デフォルト値
            assert entry.status == 'Unknown'  # デフォルト値
            
        finally:
            Path(temp_file.name).unlink()
    
    def test_search_with_invalid_criteria(self):
        """無効な検索条件のテスト"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            registry = StandardRegistry(data_file=Path(temp_file.name))
            registry.add_standard({'number': 'EN 123:2020', 'type': 'EN'})
            
            # 存在しないフィールドで検索
            result = registry.search_standards(non_existent_field='value')
            assert len(result) == 0
            
        finally:
            Path(temp_file.name).unlink()