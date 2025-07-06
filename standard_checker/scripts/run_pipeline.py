#!/usr/bin/env python3
"""
全体パイプライン実行スクリプト
PDFからの標準規格抽出とETSI情報の更新を一括実行
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.pdf_parser.parser import PDFParser
from modules.standards.registry import StandardRegistry
from modules.etsi_crawler.query import ETSICrawler
from modules.filter.filter import StandardFilter

def setup_logging(log_level: str = "INFO"):
    """ログ設定"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Standard Version Checker パイプライン")
    parser.add_argument("--input", "-i", required=True, help="入力PDFファイルパス")
    parser.add_argument("--output", "-o", help="出力ディレクトリ (デフォルト: data/output)")
    parser.add_argument("--etsi-check", action="store_true", help="ETSI情報を確認")
    parser.add_argument("--export-csv", action="store_true", help="CSV形式でエクスポート")
    parser.add_argument("--export-excel", action="store_true", help="Excel形式でエクスポート")
    parser.add_argument("--filter-status", help="特定のステータスでフィルタリング")
    parser.add_argument("--log-level", default="INFO", help="ログレベル")
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== Standard Version Checker パイプライン開始 ===")
        
        # 入力ファイルの確認
        input_file = Path(args.input)
        if not input_file.exists():
            logger.error(f"入力ファイルが見つかりません: {input_file}")
            sys.exit(1)
        
        # 出力ディレクトリの設定
        output_dir = Path(args.output) if args.output else Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ステップ1: PDFから標準規格を抽出
        logger.info("ステップ1: PDFから標準規格を抽出")
        pdf_parser = PDFParser()
        standards = pdf_parser.extract_standards_from_pdf(input_file)
        
        if not standards:
            logger.warning("標準規格が抽出されませんでした")
            sys.exit(0)
        
        logger.info(f"抽出された標準規格: {len(standards)}件")
        
        # ステップ2: 標準規格レジストリに登録
        logger.info("ステップ2: 標準規格レジストリに登録")
        registry = StandardRegistry()
        added_ids = registry.bulk_add_standards(standards)
        
        # ステップ3: ETSI情報の確認（オプション）
        if args.etsi_check:
            logger.info("ステップ3: ETSI情報を確認")
            
            with ETSICrawler(use_selenium=True) as crawler:
                for standard in standards:
                    standard_number = standard.get('number_part', '')
                    if standard_number:
                        logger.info(f"ETSI確認: {standard_number}")
                        
                        etsi_info = crawler.search_standard(standard_number)
                        
                        # レジストリを更新
                        registry.update_standard(standard['id'], {'etsi_info': etsi_info})
        
        # ステップ4: フィルタリング（オプション）
        filtered_standards = standards
        if args.filter_status:
            logger.info(f"ステップ4: ステータスでフィルタリング - {args.filter_status}")
            filter_obj = StandardFilter()
            filtered_standards = filter_obj.filter_by_status(standards, args.filter_status)
            logger.info(f"フィルタリング後: {len(filtered_standards)}件")
        
        # ステップ5: エクスポート
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"standards_{timestamp}"
        
        if args.export_csv:
            logger.info("ステップ5a: CSV形式でエクスポート")
            csv_path = output_dir / f"{base_filename}.csv"
            registry.export_to_csv(csv_path)
        
        if args.export_excel:
            logger.info("ステップ5b: Excel形式でエクスポート")
            excel_path = output_dir / f"{base_filename}.xlsx"
            registry.export_to_excel(excel_path)
        
        # 結果の保存
        pdf_parser.save_extraction_results(filtered_standards, output_dir / f"{base_filename}_results")
        
        # 統計情報の表示
        stats = registry.get_statistics()
        logger.info("=== 処理結果統計 ===")
        logger.info(f"総標準規格数: {stats['total_count']}")
        logger.info(f"タイプ別: {stats['by_type']}")
        logger.info(f"ステータス別: {stats['by_status']}")
        logger.info(f"ETSI情報有り: {stats['with_etsi_info']}")
        logger.info(f"バージョン情報有り: {stats['with_version']}")
        
        logger.info("=== パイプライン完了 ===")
        
    except Exception as e:
        logger.error(f"パイプライン実行エラー: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()