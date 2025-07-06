#!/usr/bin/env python3
"""
ETSI更新状況確認スクリプト
登録済み標準規格のETSI最新情報をチェック
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.standards.registry import StandardRegistry
from modules.etsi_crawler.query import ETSICrawler

def setup_logging(log_level: str = "INFO"):
    """ログ設定"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/update_check.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="ETSI更新状況確認")
    parser.add_argument("--force", "-f", action="store_true", help="全ての標準規格を強制的にチェック")
    parser.add_argument("--days", "-d", type=int, default=7, help="指定日数内に更新されていない標準規格をチェック")
    parser.add_argument("--standard", "-s", help="特定の標準規格番号のみチェック")
    parser.add_argument("--export", "-e", help="結果をファイルにエクスポート")
    parser.add_argument("--log-level", default="INFO", help="ログレベル")
    parser.add_argument("--delay", type=int, default=2, help="リクエスト間の待機時間（秒）")
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== ETSI更新状況確認開始 ===")
        
        # 標準規格レジストリを読み込み
        registry = StandardRegistry()
        all_standards = registry.get_all_standards()
        
        if not all_standards:
            logger.warning("登録された標準規格がありません")
            sys.exit(0)
        
        # チェック対象の標準規格を選択
        standards_to_check = []
        
        if args.standard:
            # 特定の標準規格のみ
            for standard in all_standards:
                if args.standard in standard.get('number', ''):
                    standards_to_check.append(standard)
            
            if not standards_to_check:
                logger.error(f"指定された標準規格が見つかりません: {args.standard}")
                sys.exit(1)
        
        elif args.force:
            # 全ての標準規格
            standards_to_check = all_standards
        
        else:
            # 指定日数内に更新されていない標準規格
            cutoff_date = datetime.now() - timedelta(days=args.days)
            
            for standard in all_standards:
                last_updated = standard.get('last_updated', standard.get('extracted_at', ''))
                if last_updated:
                    try:
                        update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        if update_date < cutoff_date:
                            standards_to_check.append(standard)
                    except ValueError:
                        # 日付解析エラーの場合はチェック対象に含める
                        standards_to_check.append(standard)
                else:
                    standards_to_check.append(standard)
        
        logger.info(f"チェック対象: {len(standards_to_check)}件 / 総数: {len(all_standards)}件")
        
        # ETSI情報をチェック
        update_results = []
        
        with ETSICrawler(use_selenium=True) as crawler:
            for i, standard in enumerate(standards_to_check):
                standard_number = standard.get('number_part', '')
                if not standard_number:
                    continue
                
                logger.info(f"進行状況: {i+1}/{len(standards_to_check)} - {standard_number}")
                
                try:
                    # ETSI情報を取得
                    etsi_info = crawler.search_standard(standard_number)
                    
                    # 変更があるかチェック
                    old_etsi_info = standard.get('etsi_info')
                    has_changes = _compare_etsi_info(old_etsi_info, etsi_info)
                    
                    if has_changes or not old_etsi_info:
                        # レジストリを更新
                        registry.update_standard(standard['id'], {'etsi_info': etsi_info})
                        
                        update_results.append({
                            'standard_id': standard['id'],
                            'standard_number': standard['number'],
                            'has_changes': has_changes,
                            'old_status': old_etsi_info.get('status') if old_etsi_info else None,
                            'new_status': etsi_info.get('status'),
                            'versions_count': etsi_info.get('total_versions', 0),
                            'update_time': datetime.now().isoformat()
                        })
                        
                        logger.info(f"更新検出: {standard_number} - {etsi_info.get('status', 'Unknown')}")
                    else:
                        logger.debug(f"変更なし: {standard_number}")
                
                except Exception as e:
                    logger.error(f"ETSI確認エラー ({standard_number}): {str(e)}")
                    update_results.append({
                        'standard_id': standard['id'],
                        'standard_number': standard['number'],
                        'error': str(e),
                        'update_time': datetime.now().isoformat()
                    })
                
                # レート制限
                time.sleep(args.delay)
        
        # レジストリを保存
        registry.save_data()
        
        # 結果の表示
        changes_count = sum(1 for r in update_results if r.get('has_changes', False))
        errors_count = sum(1 for r in update_results if 'error' in r)
        
        logger.info("=== 更新確認結果 ===")
        logger.info(f"チェック完了: {len(standards_to_check)}件")
        logger.info(f"変更検出: {changes_count}件")
        logger.info(f"エラー: {errors_count}件")
        
        # 変更があった標準規格の詳細
        if changes_count > 0:
            logger.info("=== 変更詳細 ===")
            for result in update_results:
                if result.get('has_changes'):
                    logger.info(f"  {result['standard_number']}: "
                              f"{result.get('old_status', 'N/A')} -> {result.get('new_status', 'N/A')}")
        
        # 結果のエクスポート
        if args.export:
            export_path = Path(args.export)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'check_time': datetime.now().isoformat(),
                    'total_checked': len(standards_to_check),
                    'changes_detected': changes_count,
                    'errors': errors_count,
                    'results': update_results
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"結果をエクスポートしました: {export_path}")
        
        logger.info("=== 更新確認完了 ===")
        
    except Exception as e:
        logger.error(f"更新確認エラー: {str(e)}")
        sys.exit(1)

def _compare_etsi_info(old_info, new_info):
    """ETSI情報の変更をチェック"""
    if not old_info and new_info:
        return True
    
    if not old_info or not new_info:
        return False
    
    # 主要フィールドの比較
    key_fields = ['status', 'total_versions']
    
    for field in key_fields:
        if old_info.get(field) != new_info.get(field):
            return True
    
    # バージョン情報の比較
    old_versions = old_info.get('versions', [])
    new_versions = new_info.get('versions', [])
    
    if len(old_versions) != len(new_versions):
        return True
    
    # 各バージョンのステータス比較
    for old_ver, new_ver in zip(old_versions, new_versions):
        if old_ver.get('status') != new_ver.get('status'):
            return True
    
    return False

if __name__ == "__main__":
    main()