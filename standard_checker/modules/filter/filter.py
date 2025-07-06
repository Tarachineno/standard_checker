"""
標準規格フィルターモジュール
条件に基づいて標準規格をフィルタリングする
"""

import re
import logging
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

class FilterOperator(Enum):
    """フィルター演算子"""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"

class StandardFilter:
    """標準規格フィルタークラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.filters = []
    
    def add_filter(self, field: str, operator: FilterOperator, value, label: str = None):
        """フィルター条件を追加"""
        filter_condition = {
            'field': field,
            'operator': operator,
            'value': value,
            'label': label or f"{field} {operator.value} {value}"
        }
        self.filters.append(filter_condition)
        return self
    
    def clear_filters(self):
        """全てのフィルターをクリア"""
        self.filters = []
        return self
    
    def apply_filters(self, standards: List[Dict], **kwargs) -> List[Dict]:
        """フィルターを適用"""
        # キーワード引数からフィルターを作成
        if kwargs:
            self._create_filters_from_kwargs(**kwargs)
        
        if not self.filters:
            return standards
        
        filtered_standards = []
        
        for standard in standards:
            if self._evaluate_standard(standard):
                filtered_standards.append(standard)
        
        self.logger.info(f"フィルター適用: {len(standards)} -> {len(filtered_standards)}件")
        return filtered_standards
    
    def _create_filters_from_kwargs(self, **kwargs):
        """キーワード引数からフィルターを作成"""
        # 一般的なフィルター条件
        filter_mappings = {
            'status': ('status', FilterOperator.EQUALS),
            'directive': ('directive', FilterOperator.CONTAINS),
            'type': ('type', FilterOperator.EQUALS),
            'source': ('source', FilterOperator.EQUALS),
            'number': ('number', FilterOperator.CONTAINS),
            'version': ('version', FilterOperator.EQUALS),
        }
        
        for key, value in kwargs.items():
            if value is None:
                continue
                
            if key in filter_mappings:
                field, operator = filter_mappings[key]
                self.add_filter(field, operator, value)
            elif key == 'date_start':
                self.add_filter('extracted_at', FilterOperator.GREATER_THAN, value)
            elif key == 'date_end':
                self.add_filter('extracted_at', FilterOperator.LESS_THAN, value)
            elif key == 'has_etsi_info':
                self.add_filter('etsi_info', FilterOperator.NOT_IN, [None, ''])
            elif key == 'has_version':
                self.add_filter('version', FilterOperator.NOT_IN, [None, ''])
    
    def _evaluate_standard(self, standard: Dict) -> bool:
        """個別の標準規格がフィルター条件を満たすかチェック"""
        for filter_condition in self.filters:
            if not self._evaluate_filter_condition(standard, filter_condition):
                return False
        return True
    
    def _evaluate_filter_condition(self, standard: Dict, filter_condition: Dict) -> bool:
        """個別のフィルター条件を評価"""
        field = filter_condition['field']
        operator = filter_condition['operator']
        filter_value = filter_condition['value']
        
        # フィールド値を取得
        standard_value = standard.get(field)
        
        # None値の処理
        if standard_value is None:
            return operator == FilterOperator.IN and None in filter_value
        
        # 演算子に応じた評価
        try:
            if operator == FilterOperator.EQUALS:
                return str(standard_value).lower() == str(filter_value).lower()
            
            elif operator == FilterOperator.CONTAINS:
                return str(filter_value).lower() in str(standard_value).lower()
            
            elif operator == FilterOperator.STARTS_WITH:
                return str(standard_value).lower().startswith(str(filter_value).lower())
            
            elif operator == FilterOperator.ENDS_WITH:
                return str(standard_value).lower().endswith(str(filter_value).lower())
            
            elif operator == FilterOperator.GREATER_THAN:
                return self._compare_values(standard_value, filter_value, '>')
            
            elif operator == FilterOperator.LESS_THAN:
                return self._compare_values(standard_value, filter_value, '<')
            
            elif operator == FilterOperator.BETWEEN:
                if len(filter_value) != 2:
                    return False
                return (self._compare_values(standard_value, filter_value[0], '>=') and 
                        self._compare_values(standard_value, filter_value[1], '<='))
            
            elif operator == FilterOperator.IN:
                return standard_value in filter_value
            
            elif operator == FilterOperator.NOT_IN:
                return standard_value not in filter_value
            
            elif operator == FilterOperator.REGEX:
                return bool(re.search(filter_value, str(standard_value), re.IGNORECASE))
            
            else:
                self.logger.warning(f"未知のフィルター演算子: {operator}")
                return True
                
        except Exception as e:
            self.logger.error(f"フィルター評価エラー: {str(e)}")
            return False
    
    def _compare_values(self, value1, value2, operator: str) -> bool:
        """値を比較"""
        try:
            # 日付の比較
            if self._is_date_string(value1) and self._is_date_string(value2):
                date1 = self._parse_date(value1)
                date2 = self._parse_date(value2)
                
                if operator == '>':
                    return date1 > date2
                elif operator == '<':
                    return date1 < date2
                elif operator == '>=':
                    return date1 >= date2
                elif operator == '<=':
                    return date1 <= date2
            
            # 数値の比較
            elif self._is_numeric(value1) and self._is_numeric(value2):
                num1 = float(value1)
                num2 = float(value2)
                
                if operator == '>':
                    return num1 > num2
                elif operator == '<':
                    return num1 < num2
                elif operator == '>=':
                    return num1 >= num2
                elif operator == '<=':
                    return num1 <= num2
            
            # 文字列の比較
            else:
                str1 = str(value1).lower()
                str2 = str(value2).lower()
                
                if operator == '>':
                    return str1 > str2
                elif operator == '<':
                    return str1 < str2
                elif operator == '>=':
                    return str1 >= str2
                elif operator == '<=':
                    return str1 <= str2
            
            return False
            
        except Exception as e:
            self.logger.error(f"値比較エラー: {str(e)}")
            return False
    
    def _is_date_string(self, value: str) -> bool:
        """文字列が日付形式かチェック"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, str(value)):
                return True
        return False
    
    def _parse_date(self, date_string: str) -> datetime:
        """日付文字列をdatetimeオブジェクトに変換"""
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y',
            '%d.%m.%Y',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # フォーマットが一致しない場合はデフォルト値
        return datetime.min
    
    def _is_numeric(self, value) -> bool:
        """値が数値かチェック"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def filter_by_status(self, standards: List[Dict], status: str) -> List[Dict]:
        """ステータスでフィルタリング"""
        return [s for s in standards if s.get('status', '').lower() == status.lower()]
    
    def filter_by_directive(self, standards: List[Dict], directive: str) -> List[Dict]:
        """指令でフィルタリング"""
        return [s for s in standards if s.get('directive') and directive.lower() in s.get('directive', '').lower()]
    
    def filter_by_date_range(self, standards: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """日付範囲でフィルタリング"""
        try:
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            
            filtered = []
            for standard in standards:
                extracted_at = standard.get('extracted_at', '')
                if extracted_at:
                    standard_dt = self._parse_date(extracted_at)
                    if start_dt <= standard_dt <= end_dt:
                        filtered.append(standard)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"日付範囲フィルターエラー: {str(e)}")
            return standards
    
    def filter_by_type(self, standards: List[Dict], standard_type: str) -> List[Dict]:
        """標準規格タイプでフィルタリング"""
        return [s for s in standards if s.get('type', '').lower() == standard_type.lower()]
    
    def filter_by_version_exists(self, standards: List[Dict], has_version: bool = True) -> List[Dict]:
        """バージョン情報の有無でフィルタリング"""
        if has_version:
            return [s for s in standards if s.get('version') not in [None, '', 'null']]
        else:
            return [s for s in standards if s.get('version') in [None, '', 'null']]
    
    def filter_by_etsi_info_exists(self, standards: List[Dict], has_etsi_info: bool = True) -> List[Dict]:
        """ETSI情報の有無でフィルタリング"""
        if has_etsi_info:
            return [s for s in standards if s.get('etsi_info') not in [None, '', {}]]
        else:
            return [s for s in standards if s.get('etsi_info') in [None, '', {}]]
    
    def create_custom_filter(self, filter_func: Callable[[Dict], bool], label: str = "Custom Filter"):
        """カスタムフィルターを作成"""
        return lambda standards: [s for s in standards if filter_func(s)]
    
    def get_filter_summary(self) -> Dict:
        """適用されているフィルターの概要を取得"""
        return {
            'total_filters': len(self.filters),
            'filters': [
                {
                    'field': f['field'],
                    'operator': f['operator'].value,
                    'value': f['value'],
                    'label': f['label']
                }
                for f in self.filters
            ]
        }
    
    def export_filtered_results(self, filtered_standards: List[Dict], output_path: str):
        """フィルタリング結果をエクスポート"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(filtered_standards)
            
            if output_path.endswith('.csv'):
                df.to_csv(output_path, index=False)
            elif output_path.endswith('.xlsx'):
                df.to_excel(output_path, index=False)
            else:
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_standards, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"フィルタリング結果をエクスポート: {output_path}")
            
        except Exception as e:
            self.logger.error(f"エクスポートエラー: {str(e)}")
            raise