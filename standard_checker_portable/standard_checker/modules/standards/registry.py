"""
標準規格レジストリ
標準規格データの管理と操作を行う
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class StandardEntry:
    """個別の標準規格情報を管理するクラス"""
    
    def __init__(self, data: Dict):
        self.id = data.get('id', str(uuid.uuid4()))
        self.number = data.get('number', '')
        self.type = data.get('type', '')
        self.number_part = data.get('number_part', '')
        self.version = data.get('version', None)
        self.status = data.get('status', 'Unknown')
        self.directive = data.get('directive', None)
        self.extracted_at = data.get('extracted_at', datetime.now().isoformat())
        self.source = data.get('source', 'Manual')
        self.etsi_info = data.get('etsi_info', None)
        self.last_updated = data.get('last_updated', datetime.now().isoformat())
        self.notes = data.get('notes', '')
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'number': self.number,
            'type': self.type,
            'number_part': self.number_part,
            'version': self.version,
            'status': self.status,
            'directive': self.directive,
            'extracted_at': self.extracted_at,
            'source': self.source,
            'etsi_info': self.etsi_info,
            'last_updated': self.last_updated,
            'notes': self.notes
        }
    
    def update_etsi_info(self, etsi_info: Dict):
        """ETSI情報を更新"""
        self.etsi_info = etsi_info
        self.last_updated = datetime.now().isoformat()
    
    def update_status(self, status: str):
        """ステータスを更新"""
        self.status = status
        self.last_updated = datetime.now().isoformat()


class StandardRegistry:
    """標準規格レジストリクラス"""
    
    def __init__(self, data_file: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.data_file = data_file or Path("data/output/standards_registry.json")
        self.standards: Dict[str, StandardEntry] = {}
        self.load_data()
    
    def load_data(self):
        """保存されたデータを読み込み"""
        try:
            if self.data_file.exists() and self.data_file.stat().st_size > 0:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        entry = StandardEntry(item)
                        self.standards[entry.id] = entry
                self.logger.info(f"{len(self.standards)}件の標準規格を読み込みました")
            else:
                self.logger.info("新規レジストリを作成します")
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {str(e)}")
            self.standards = {}
    
    def save_data(self):
        """データを保存"""
        try:
            # 出力ディレクトリを作成
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            # データを辞書のリストに変換
            data = [entry.to_dict() for entry in self.standards.values()]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"データを保存しました: {self.data_file}")
            
        except Exception as e:
            self.logger.error(f"データ保存エラー: {str(e)}")
            raise
    
    def add_standard(self, standard_data: Dict) -> str:
        """標準規格を追加"""
        try:
            # 既存の標準規格をチェック
            existing_id = self._find_existing_standard(standard_data)
            
            if existing_id:
                # 既存の標準規格を更新
                self.standards[existing_id].last_updated = datetime.now().isoformat()
                self.logger.info(f"既存標準規格を更新: {standard_data.get('number', '')}")
                return existing_id
            else:
                # 新規標準規格を追加
                entry = StandardEntry(standard_data)
                self.standards[entry.id] = entry
                self.logger.info(f"新規標準規格を追加: {entry.number}")
                return entry.id
                
        except Exception as e:
            self.logger.error(f"標準規格追加エラー: {str(e)}")
            raise
    
    def _find_existing_standard(self, standard_data: Dict) -> Optional[str]:
        """既存の標準規格を検索"""
        search_number = standard_data.get('number', '')
        search_type = standard_data.get('type', '')
        search_version = standard_data.get('version', None)
        
        for entry_id, entry in self.standards.items():
            if (entry.number == search_number or 
                (entry.type == search_type and 
                 entry.number_part == standard_data.get('number_part', '') and
                 str(entry.version) == str(search_version))):
                return entry_id
        
        return None
    
    def get_standard(self, standard_id: str) -> Optional[StandardEntry]:
        """指定されたIDの標準規格を取得"""
        return self.standards.get(standard_id)
    
    def get_all_standards(self) -> List[Dict]:
        """全ての標準規格を取得"""
        return [entry.to_dict() for entry in self.standards.values()]
    
    def remove_standard(self, standard_id: str) -> bool:
        """標準規格を削除"""
        if standard_id in self.standards:
            del self.standards[standard_id]
            self.logger.info(f"標準規格を削除: {standard_id}")
            return True
        return False
    
    def update_standard(self, standard_id: str, update_data: Dict) -> bool:
        """標準規格を更新"""
        if standard_id not in self.standards:
            return False
        
        entry = self.standards[standard_id]
        
        # 更新可能なフィールドを更新
        updatable_fields = ['status', 'directive', 'notes', 'etsi_info']
        
        for field in updatable_fields:
            if field in update_data:
                setattr(entry, field, update_data[field])
        
        entry.last_updated = datetime.now().isoformat()
        self.logger.info(f"標準規格を更新: {standard_id}")
        return True
    
    def search_standards(self, **criteria) -> List[Dict]:
        """条件に基づいて標準規格を検索"""
        results = []
        
        for entry in self.standards.values():
            match = True
            
            # 各検索条件をチェック
            for key, value in criteria.items():
                if not hasattr(entry, key):
                    continue
                
                entry_value = getattr(entry, key)
                
                # 文字列の部分一致検索
                if isinstance(value, str) and isinstance(entry_value, str):
                    if value.lower() not in entry_value.lower():
                        match = False
                        break
                # 完全一致検索
                elif entry_value != value:
                    match = False
                    break
            
            if match:
                results.append(entry.to_dict())
        
        return results
    
    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        stats = {
            'total_count': len(self.standards),
            'by_type': {},
            'by_status': {},
            'by_source': {},
            'with_etsi_info': 0,
            'with_version': 0
        }
        
        for entry in self.standards.values():
            # タイプ別集計
            stats['by_type'][entry.type] = stats['by_type'].get(entry.type, 0) + 1
            
            # ステータス別集計
            stats['by_status'][entry.status] = stats['by_status'].get(entry.status, 0) + 1
            
            # ソース別集計
            stats['by_source'][entry.source] = stats['by_source'].get(entry.source, 0) + 1
            
            # ETSI情報有無
            if entry.etsi_info:
                stats['with_etsi_info'] += 1
            
            # バージョン情報有無
            if entry.version:
                stats['with_version'] += 1
        
        return stats
    
    def bulk_add_standards(self, standards_list: List[Dict]) -> List[str]:
        """複数の標準規格を一括追加"""
        added_ids = []
        
        for standard_data in standards_list:
            try:
                standard_id = self.add_standard(standard_data)
                added_ids.append(standard_id)
            except Exception as e:
                self.logger.error(f"一括追加エラー: {str(e)}")
                continue
        
        # データを保存
        self.save_data()
        
        self.logger.info(f"{len(added_ids)}件の標準規格を一括追加しました")
        return added_ids
    
    def export_to_csv(self, output_path: Path):
        """CSV形式でエクスポート"""
        try:
            import pandas as pd
            
            data = self.get_all_standards()
            df = pd.DataFrame(data)
            
            # 出力ディレクトリを作成
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            self.logger.info(f"CSVエクスポート完了: {output_path}")
            
        except Exception as e:
            self.logger.error(f"CSVエクスポートエラー: {str(e)}")
            raise
    
    def export_to_excel(self, output_path: Path):
        """Excel形式でエクスポート"""
        try:
            import pandas as pd
            
            data = self.get_all_standards()
            df = pd.DataFrame(data)
            
            # 出力ディレクトリを作成
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Standards', index=False)
                
                # 統計情報も追加
                stats = self.get_statistics()
                stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            self.logger.info(f"Excelエクスポート完了: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Excelエクスポートエラー: {str(e)}")
            raise