"""
ETSIポータルクローラー
ETSIのWEBポータルから標準規格の最新情報を取得する
"""

import time
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ETSICrawler:
    """ETSIポータルクローラークラス"""
    
    def __init__(self, use_selenium: bool = True):
        self.logger = logging.getLogger(__name__)
        self.use_selenium = use_selenium
        self.base_url = "https://portal.etsi.org"
        self.search_url = "https://portal.etsi.org/webapp/WorkProgram/Frame_WorkItemList.asp"
        self.session = requests.Session()
        self.driver = None
        self._user_data_dir = None  # 追加: user-data-dirのパス
        # リクエストヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def __enter__(self):
        if self.use_selenium:
            self._setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import shutil
        if self.driver:
            self.driver.quit()
        if self._user_data_dir:
            shutil.rmtree(self._user_data_dir, ignore_errors=True)
            self._user_data_dir = None
    
    def _setup_driver(self):
        """Seleniumドライバーのセットアップ"""
        import tempfile
        import shutil
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # 毎回一意なuser-data-dirを指定
        self._user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f'--user-data-dir={self._user_data_dir}')
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.logger.info("Selenium Chromeドライバーを初期化しました")
        except Exception as e:
            # 失敗時はディレクトリを削除
            if self._user_data_dir:
                shutil.rmtree(self._user_data_dir, ignore_errors=True)
                self._user_data_dir = None
            self.logger.error(f"Seleniumドライバー初期化エラー: {str(e)}")
            raise
    
    def search_standard(self, standard_number: str) -> Dict:
        """
        指定された標準規格番号でETSIポータルを検索
        
        Args:
            standard_number: 標準規格番号 (例: "301 489-17")
            
        Returns:
            検索結果の辞書
        """
        try:
            self.logger.info(f"ETSI検索開始: {standard_number}")
            
            # 標準規格番号を正規化
            normalized_number = self._normalize_standard_number(standard_number)
            
            if self.use_selenium:
                result = self._search_with_selenium(normalized_number)
            else:
                result = self._search_with_requests(normalized_number)
            
            self.logger.info(f"ETSI検索完了: {standard_number}")
            return result
            
        except Exception as e:
            self.logger.error(f"ETSI検索エラー: {str(e)}")
            return {
                'standard_number': standard_number,
                'error': str(e),
                'status': 'Error',
                'versions': []
            }
    
    def _normalize_standard_number(self, standard_number: str) -> str:
        """標準規格番号を正規化"""
        # 一般的な形式に変換
        normalized = standard_number.strip()
        
        # "EN 301 489-17:2017" -> "301 489-17"
        # "ETSI EN 301 489-17" -> "301 489-17"
        patterns = [
            r'ETSI\s+EN\s+(\d+(?:\s+\d+)*(?:-\d+)*)',
            r'EN\s+(\d+(?:\s+\d+)*(?:-\d+)*)',
            r'(\d+(?:\s+\d+)*(?:-\d+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return match.group(1)
        
        return normalized
    
    def _search_with_selenium(self, standard_number: str) -> Dict:
        """Seleniumを使用してETSIポータルを検索"""
        try:
            if not self.driver:
                self._setup_driver()
            
            # 検索ページに移動
            self.driver.get(self.search_url)
            
            # 検索フォームの入力
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "qETSIDeliverableNumber"))
            )
            search_input.clear()
            search_input.send_keys(standard_number)
            
            # All Versionsをチェック
            try:
                all_versions_checkbox = self.driver.find_element(By.NAME, "qETSIAllVersions")
                if not all_versions_checkbox.is_selected():
                    all_versions_checkbox.click()
            except NoSuchElementException:
                self.logger.warning("All Versionsチェックボックスが見つかりません")
            
            # 検索実行
            search_button = self.driver.find_element(By.NAME, "qETSISearchButton")
            search_button.click()
            
            # 結果が表示されるまで待機
            time.sleep(3)
            
            # 結果テーブルを解析
            return self._parse_search_results_selenium()
            
        except TimeoutException:
            self.logger.error("ETSIポータルの応答がタイムアウトしました")
            return {
                'standard_number': standard_number,
                'error': 'Timeout',
                'status': 'Error',
                'versions': []
            }
        except Exception as e:
            self.logger.error(f"Selenium検索エラー: {str(e)}")
            raise
    
    def _search_with_requests(self, standard_number: str) -> Dict:
        """requestsを使用してETSIポータルを検索"""
        try:
            # 検索パラメータ（実際のクエリに合わせて修正）
            params = {
                'SearchPage': 'TRUE',
                'qETSI_STANDARD_TYPE': '',
                'qETSI_NUMBER': standard_number,
                'qTB_ID': '',
                'qINCLUDE_SUB_TB': 'TRUE',
                'includeNonActiveTB': 'FALSE',
                'qWKI_REFERENCE': '',
                'qTITLE': '',
                'qSCOPE': '',
                'qCURRENT_STATE_CODE': '',
                'qSTOP_FLG': 'N',
                'qSTART_CURRENT_STATUS_CODE': '',
                'qEND_CURRENT_STATUS_CODE': '',
                'qFROM_MIL_DAY': '',
                'qFROM_MIL_MONTH': '',
                'qFROM_MIL_YEAR': '',
                'qTO_MIL_DAY': '',
                'qTO_MIL_MONTH': '',
                'qTO_MIL_YEAR': '',
                'qOPERATOR_TS': '',
                'qRAPTR_NAME': '',
                'qRAPTR_ORGANISATION': '',
                'qKEYWORD_BOOLEAN': 'OR',
                'qKEYWORD': '',
                'qPROJECT_BOOLEAN': 'OR',
                'qPROJECT_CODE': '',
                'includeSubProjectCode': 'FALSE',
                'qSTF_List': '',
                'qDIRECTIVE': '',
                'qMandate_List': '',
                'qCLUSTER_BOOLEAN': 'OR',
                'qCLUSTER': '',
                'qFREQUENCIES_BOOLEAN': 'OR',
                'qFREQUENCIES': '',
                'qFreqLow': '',
                'qFreqLowUnit': '1000',
                'qFreqHigh': '',
                'qFreqHighUnit': '1000',
                'AspectComments': '',
                'qSORT': 'HIGHVERSION',
                'qREPORT_TYPE': 'SUMMARY',
                'optDisplay': '10',
                'titleType': 'all',
                'butExpertSearch': '  Search  '
            }
            from urllib.parse import urlencode
            print("[ETSIクエリ] " + self.search_url + "?" + urlencode(params))
            # 検索実行
            response = self.session.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            # 結果を解析
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_search_results_requests(soup, standard_number)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP検索エラー: {str(e)}")
            return {
                'standard_number': standard_number,
                'error': str(e),
                'status': 'Error',
                'versions': []
            }
    
    def _parse_search_results_selenium(self) -> Dict:
        """Seleniumで取得した検索結果を解析"""
        try:
            # 結果テーブルを取得
            table = self.driver.find_element(By.CLASS_NAME, "report-table")
            
            # HTMLを取得してBeautifulSoupで解析
            table_html = table.get_attribute('outerHTML')
            soup = BeautifulSoup(table_html, 'html.parser')
            
            return self._parse_results_table(soup)
            
        except NoSuchElementException:
            return {
                'status': 'No Results',
                'versions': [],
                'message': '検索結果が見つかりませんでした'
            }
    
    def _parse_search_results_requests(self, soup: BeautifulSoup, standard_number: str) -> Dict:
        """requestsで取得した検索結果を解析"""
        return self._parse_results_table(soup)
    
    def _parse_results_table(self, soup: BeautifulSoup) -> Dict:
        """結果テーブルを解析"""
        try:
            # テーブルを検索
            table = soup.find('table', class_='report-table') or soup.find('table')
            
            if not table:
                return {
                    'status': 'No Results',
                    'versions': [],
                    'message': 'テーブルが見つかりませんでした'
                }
            
            # ヘッダー行を取得
            header_row = table.find('tr')
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # データ行を取得
            data_rows = table.find_all('tr')[1:]  # ヘッダー行を除く
            
            versions = []
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers):
                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.get_text(strip=True)
                    
                    # 必要な情報を抽出
                    version_info = {
                        'identification': row_data.get('IDENTIFICATION', ''),
                        'status': row_data.get('STATUS', ''),
                        'publication_date': row_data.get('PUBLICATION DATE', ''),
                        'oj_reference': row_data.get('OJ REFERENCE', ''),
                        'title': row_data.get('TITLE', ''),
                        'raw_data': row_data
                    }
                    
                    versions.append(version_info)
            
            return {
                'status': 'Success',
                'versions': versions,
                'total_versions': len(versions),
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"テーブル解析エラー: {str(e)}")
            return {
                'status': 'Parse Error',
                'versions': [],
                'error': str(e)
            }
    
    def get_standard_details(self, standard_url: str) -> Dict:
        """標準規格の詳細情報を取得"""
        try:
            if self.use_selenium:
                self.driver.get(standard_url)
                time.sleep(2)
                
                # 詳細情報を取得
                details = {}
                
                # 基本情報
                try:
                    title_element = self.driver.find_element(By.CLASS_NAME, "standard-title")
                    details['title'] = title_element.text
                except NoSuchElementException:
                    pass
                
                # 状態情報
                try:
                    status_element = self.driver.find_element(By.CLASS_NAME, "standard-status")
                    details['status'] = status_element.text
                except NoSuchElementException:
                    pass
                
                return details
                
            else:
                response = self.session.get(standard_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 詳細情報を抽出
                details = {
                    'url': standard_url,
                    'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
                    'content': soup.get_text(strip=True)[:500]  # 最初の500文字
                }
                
                return details
                
        except Exception as e:
            self.logger.error(f"詳細情報取得エラー: {str(e)}")
            return {'error': str(e)}
    
    def batch_search_standards(self, standard_numbers: List[str]) -> List[Dict]:
        """複数の標準規格を一括検索"""
        results = []
        
        for i, standard_number in enumerate(standard_numbers):
            self.logger.info(f"一括検索進行中: {i+1}/{len(standard_numbers)} - {standard_number}")
            
            result = self.search_standard(standard_number)
            results.append(result)
            
            # レート制限のための待機
            time.sleep(2)
        
        return results
    
    def export_search_results(self, results: List[Dict], output_path: str):
        """検索結果をエクスポート"""
        try:
            # 結果を平坦化
            flattened_results = []
            
            for result in results:
                base_info = {
                    'standard_number': result.get('standard_number', ''),
                    'search_status': result.get('status', ''),
                    'total_versions': result.get('total_versions', 0),
                    'last_updated': result.get('last_updated', ''),
                    'error': result.get('error', '')
                }
                
                versions = result.get('versions', [])
                if versions:
                    for version in versions:
                        row = {**base_info, **version}
                        flattened_results.append(row)
                else:
                    flattened_results.append(base_info)
            
            # DataFrameに変換してエクスポート
            df = pd.DataFrame(flattened_results)
            
            if output_path.endswith('.csv'):
                df.to_csv(output_path, index=False)
            elif output_path.endswith('.xlsx'):
                df.to_excel(output_path, index=False)
            else:
                # JSONとして保存
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"検索結果をエクスポートしました: {output_path}")
            
        except Exception as e:
            self.logger.error(f"エクスポートエラー: {str(e)}")
            raise