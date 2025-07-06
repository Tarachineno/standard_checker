"""
フィルターモジュールの単体テスト
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.filter.filter import StandardFilter, FilterOperator

class TestStandardFilter:
    """StandardFilterクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.filter = StandardFilter()
        self.sample_standards = [
            {
                'id': '1',
                'number': 'EN 301 489-17:2017',
                'type': 'EN',
                'number_part': '301 489-17',
                'version': '2017',
                'status': 'Active',
                'directive': 'RED 2014/53/EU',
                'extracted_at': '2023-01-15T10:00:00',
                'source': 'PDF',
                'etsi_info': {'status': 'Published'},
                'notes': 'Test note 1'
            },
            {
                'id': '2',
                'number': 'IEC 62368-1:2014',
                'type': 'IEC',
                'number_part': '62368-1',
                'version': '2014',
                'status': 'Withdrawn',
                'directive': 'LVD 2014/35/EU',
                'extracted_at': '2023-02-20T15:30:00',
                'source': 'Manual',
                'etsi_info': None,
                'notes': 'Test note 2'
            },
            {
                'id': '3',
                'number': 'ISO 9001:2015',
                'type': 'ISO',
                'number_part': '9001',
                'version': '2015',
                'status': 'Active',
                'directive': None,
                'extracted_at': '2023-03-10T08:45:00',
                'source': 'PDF',
                'etsi_info': {'status': 'Current'},
                'notes': ''
            },
            {
                'id': '4',
                'number': 'EN 55032:2015',
                'type': 'EN',
                'number_part': '55032',
                'version': None,
                'status': 'Active',
                'directive': 'EMC 2014/30/EU',
                'extracted_at': '2023-04-05T12:00:00',
                'source': 'PDF',
                'etsi_info': None,
                'notes': 'No version specified'
            }
        ]
    
    def test_add_filter(self):
        """フィルター追加テスト"""
        self.filter.add_filter('status', FilterOperator.EQUALS, 'Active')
        
        assert len(self.filter.filters) == 1
        assert self.filter.filters[0]['field'] == 'status'
        assert self.filter.filters[0]['operator'] == FilterOperator.EQUALS
        assert self.filter.filters[0]['value'] == 'Active'
    
    def test_clear_filters(self):
        """フィルタークリアテスト"""
        self.filter.add_filter('status', FilterOperator.EQUALS, 'Active')
        self.filter.add_filter('type', FilterOperator.EQUALS, 'EN')
        
        assert len(self.filter.filters) == 2
        
        self.filter.clear_filters()
        assert len(self.filter.filters) == 0
    
    def test_filter_by_status(self):
        """ステータスフィルターテスト"""
        result = self.filter.filter_by_status(self.sample_standards, 'Active')
        
        assert len(result) == 3
        assert all(s['status'] == 'Active' for s in result)
        
        withdrawn_result = self.filter.filter_by_status(self.sample_standards, 'Withdrawn')
        assert len(withdrawn_result) == 1
        assert withdrawn_result[0]['status'] == 'Withdrawn'
    
    def test_filter_by_directive(self):
        """指令フィルターテスト"""
        result = self.filter.filter_by_directive(self.sample_standards, 'RED')
        
        assert len(result) == 1
        assert 'RED' in result[0]['directive']
        
        eu_result = self.filter.filter_by_directive(self.sample_standards, '2014')
        assert len(eu_result) == 3  # RED, LVD, EMC
    
    def test_filter_by_type(self):
        """タイプフィルターテスト"""
        result = self.filter.filter_by_type(self.sample_standards, 'EN')
        
        assert len(result) == 2
        assert all(s['type'] == 'EN' for s in result)
    
    def test_filter_by_version_exists(self):
        """バージョン存在フィルターテスト"""
        # バージョン有りでフィルタリング
        with_version = self.filter.filter_by_version_exists(self.sample_standards, True)
        assert len(with_version) == 3
        assert all(s['version'] not in [None, '', 'null'] for s in with_version)
        
        # バージョン無しでフィルタリング
        without_version = self.filter.filter_by_version_exists(self.sample_standards, False)
        assert len(without_version) == 1
        assert without_version[0]['version'] is None
    
    def test_filter_by_etsi_info_exists(self):
        """ETSI情報存在フィルターテスト"""
        # ETSI情報有りでフィルタリング
        with_etsi = self.filter.filter_by_etsi_info_exists(self.sample_standards, True)
        assert len(with_etsi) == 2
        assert all(s['etsi_info'] not in [None, '', {}] for s in with_etsi)
        
        # ETSI情報無しでフィルタリング
        without_etsi = self.filter.filter_by_etsi_info_exists(self.sample_standards, False)
        assert len(without_etsi) == 2
        assert all(s['etsi_info'] in [None, '', {}] for s in without_etsi)
    
    def test_apply_filters_with_kwargs(self):
        """キーワード引数でのフィルター適用テスト"""
        # ステータスでフィルタリング
        result = self.filter.apply_filters(self.sample_standards, status='Active')
        assert len(result) == 3
        assert all(s['status'] == 'Active' for s in result)
        
        # タイプとステータスの組み合わせ
        self.filter.clear_filters()
        result = self.filter.apply_filters(self.sample_standards, type='EN', status='Active')
        assert len(result) == 2
        assert all(s['type'] == 'EN' and s['status'] == 'Active' for s in result)
    
    def test_apply_filters_with_manual_filters(self):
        """手動フィルター追加でのテスト"""
        self.filter.add_filter('type', FilterOperator.EQUALS, 'EN')
        self.filter.add_filter('status', FilterOperator.EQUALS, 'Active')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 2
        assert all(s['type'] == 'EN' and s['status'] == 'Active' for s in result)
    
    def test_filter_operator_contains(self):
        """CONTAINS演算子テスト"""
        self.filter.add_filter('number', FilterOperator.CONTAINS, '301 489')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 1
        assert '301 489' in result[0]['number']
    
    def test_filter_operator_starts_with(self):
        """STARTS_WITH演算子テスト"""
        self.filter.add_filter('number', FilterOperator.STARTS_WITH, 'EN')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 2
        assert all(s['number'].startswith('EN') for s in result)
    
    def test_filter_operator_in(self):
        """IN演算子テスト"""
        self.filter.add_filter('type', FilterOperator.IN, ['EN', 'IEC'])
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 3
        assert all(s['type'] in ['EN', 'IEC'] for s in result)
    
    def test_filter_operator_not_in(self):
        """NOT_IN演算子テスト"""
        self.filter.add_filter('status', FilterOperator.NOT_IN, ['Withdrawn'])
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 3
        assert all(s['status'] != 'Withdrawn' for s in result)
    
    def test_filter_operator_regex(self):
        """REGEX演算子テスト"""
        self.filter.add_filter('number', FilterOperator.REGEX, r'EN\s+\d+')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 2
        # EN標準規格のみが一致するはず
        assert all(s['type'] == 'EN' for s in result)
    
    def test_date_range_filter(self):
        """日付範囲フィルターテスト"""
        start_date = '2023-02-01'
        end_date = '2023-03-31'
        
        result = self.filter.filter_by_date_range(self.sample_standards, start_date, end_date)
        
        assert len(result) == 2  # 2023-02-20 と 2023-03-10
        
        # 抽出された日付が範囲内かチェック
        for standard in result:
            extracted_date = datetime.fromisoformat(standard['extracted_at'])
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            assert start_dt <= extracted_date <= end_dt
    
    def test_numeric_comparison(self):
        """数値比較テスト"""
        # バージョンを数値として比較
        self.filter.add_filter('version', FilterOperator.GREATER_THAN, '2014')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        # 2015, 2017が該当
        version_numbers = [s['version'] for s in result if s['version']]
        assert all(int(v) > 2014 for v in version_numbers)
    
    def test_between_operator(self):
        """BETWEEN演算子テスト"""
        self.filter.add_filter('version', FilterOperator.BETWEEN, ['2014', '2016'])
        
        result = self.filter.apply_filters(self.sample_standards)
        
        # 2014, 2015が該当
        assert len(result) == 2
        version_numbers = [int(s['version']) for s in result if s['version']]
        assert all(2014 <= v <= 2016 for v in version_numbers)
    
    def test_multiple_filters(self):
        """複数フィルター組み合わせテスト"""
        self.filter.add_filter('type', FilterOperator.EQUALS, 'EN')
        self.filter.add_filter('status', FilterOperator.EQUALS, 'Active')
        self.filter.add_filter('source', FilterOperator.EQUALS, 'PDF')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 2
        for standard in result:
            assert standard['type'] == 'EN'
            assert standard['status'] == 'Active'
            assert standard['source'] == 'PDF'
    
    def test_filter_with_none_values(self):
        """None値を含むフィルターテスト"""
        # directiveがNoneの標準規格をフィルタリング
        self.filter.add_filter('directive', FilterOperator.IN, [None])
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 1
        assert result[0]['directive'] is None
    
    def test_case_insensitive_filtering(self):
        """大文字小文字を区別しないフィルターテスト"""
        # 小文字で検索
        self.filter.add_filter('status', FilterOperator.EQUALS, 'active')
        
        result = self.filter.apply_filters(self.sample_standards)
        
        assert len(result) == 3  # 'Active'の標準規格が一致
    
    def test_get_filter_summary(self):
        """フィルター概要取得テスト"""
        self.filter.add_filter('type', FilterOperator.EQUALS, 'EN', 'EN Standards')
        self.filter.add_filter('status', FilterOperator.CONTAINS, 'Active', 'Active Status')
        
        summary = self.filter.get_filter_summary()
        
        assert summary['total_filters'] == 2
        assert len(summary['filters']) == 2
        
        filter_info = summary['filters'][0]
        assert filter_info['field'] == 'type'
        assert filter_info['operator'] == 'equals'
        assert filter_info['value'] == 'EN'
        assert filter_info['label'] == 'EN Standards'
    
    def test_create_custom_filter(self):
        """カスタムフィルター作成テスト"""
        # バージョンが2015以上の標準規格
        custom_filter = self.filter.create_custom_filter(
            lambda s: s.get('version') and int(s['version']) >= 2015,
            "Version 2015+"
        )
        
        result = custom_filter(self.sample_standards)
        
        assert len(result) == 2  # 2015, 2017
        version_numbers = [int(s['version']) for s in result]
        assert all(v >= 2015 for v in version_numbers)
    
    def test_is_date_string(self):
        """日付文字列判定テスト"""
        assert self.filter._is_date_string('2023-01-15')
        assert self.filter._is_date_string('2023-01-15T10:00:00')
        assert self.filter._is_date_string('01/15/2023')
        assert self.filter._is_date_string('15.01.2023')
        assert not self.filter._is_date_string('not a date')
        assert not self.filter._is_date_string('2023')
    
    def test_is_numeric(self):
        """数値判定テスト"""
        assert self.filter._is_numeric('123')
        assert self.filter._is_numeric('123.45')
        assert self.filter._is_numeric('-123')
        assert self.filter._is_numeric('0')
        assert not self.filter._is_numeric('abc')
        assert not self.filter._is_numeric('')
        assert not self.filter._is_numeric(None)
    
    def test_parse_date(self):
        """日付解析テスト"""
        # ISO形式
        date1 = self.filter._parse_date('2023-01-15')
        assert date1.year == 2023
        assert date1.month == 1
        assert date1.day == 15
        
        # ISO形式（時刻付き）
        date2 = self.filter._parse_date('2023-01-15T10:30:00')
        assert date2.hour == 10
        assert date2.minute == 30
        
        # 不正な形式
        date3 = self.filter._parse_date('invalid date')
        assert date3 == datetime.min

class TestFilterOperatorEdgeCases:
    """フィルター演算子のエッジケーステスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.filter = StandardFilter()
        self.test_data = [
            {'field1': '', 'field2': 0, 'field3': None},
            {'field1': 'value', 'field2': 100, 'field3': 'text'}
        ]
    
    def test_empty_string_filtering(self):
        """空文字列フィルターテスト"""
        self.filter.add_filter('field1', FilterOperator.EQUALS, '')
        
        result = self.filter.apply_filters(self.test_data)
        
        assert len(result) == 1
        assert result[0]['field1'] == ''
    
    def test_zero_value_filtering(self):
        """ゼロ値フィルターテスト"""
        self.filter.add_filter('field2', FilterOperator.EQUALS, 0)
        
        result = self.filter.apply_filters(self.test_data)
        
        assert len(result) == 1
        assert result[0]['field2'] == 0
    
    def test_none_value_filtering(self):
        """None値フィルターテスト"""
        self.filter.add_filter('field3', FilterOperator.IN, [None])
        
        result = self.filter.apply_filters(self.test_data)
        
        assert len(result) == 1
        assert result[0]['field3'] is None
    
    def test_invalid_field_filtering(self):
        """存在しないフィールドのフィルターテスト"""
        self.filter.add_filter('non_existent_field', FilterOperator.EQUALS, 'value')
        
        result = self.filter.apply_filters(self.test_data)
        
        # 存在しないフィールドはNoneとして扱われる
        assert len(result) == 0