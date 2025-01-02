"""
TDnetサイトの操作例（非ヘッドレスモード）
HTMLログ出力付き
"""
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import os
from datetime import datetime
import json
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import presence_of_element_located, frame_to_be_available_and_switch_to_it, visibility_of_element_located
import traceback

# ロガーの設定
log_dir = "backend/app/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"tdnet_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def wait_for_element(driver, by, value, timeout=10):
    """要素の待機"""
    try:
        element = WebDriverWait(driver, timeout).until(
            presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logger.error(f"Timeout waiting for element: {value}")
        return None

def wait_for_visible_element(driver, by, value, timeout=10):
    """可視要素の待機"""
    try:
        element = WebDriverWait(driver, timeout).until(
            visibility_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logger.error(f"Timeout waiting for visible element: {value}")
        return None

def save_debug_info(driver, prefix="debug"):
    """デバッグ情報の保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # スクリーンショットを保存
    screenshot_path = os.path.join(log_dir, f"{prefix}_screenshot_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    logger.info(f"Screenshot saved: {screenshot_path}")
    
    # ページソースを保存
    source_path = os.path.join(log_dir, f"{prefix}_source_{timestamp}.html")
    with open(source_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logger.info(f"Page source saved: {source_path}")
    
    return screenshot_path, source_path

def find_result_table(driver, max_attempts=10, wait_time=5, current_depth=0):
    """検索結果のテーブルを探す（再帰的にiframeを探索）"""
    logger.info("=" * 40)
    logger.info(f"Looking for result table (depth: {current_depth})")
    logger.info("=" * 40)
    
    for attempt in range(max_attempts):
        logger.info(f"Attempt {attempt + 1} of {max_attempts}")
        
        try:
            # 現在のフレームのHTMLをログに記録
            current_html = driver.page_source
            logger.info(f"Current frame HTML structure (depth: {current_depth}):")
            logger.info("=" * 80)
            logger.info(current_html)
            logger.info("=" * 80)
            
            # BeautifulSoupでHTMLを解析
            soup = BeautifulSoup(current_html, 'html.parser')
            logger.info(f"Current frame parsed structure (depth: {current_depth}):")
            logger.info("=" * 80)
            logger.info(soup.prettify())
            logger.info("=" * 80)
            
            # まずこのフレーム内のテーブルを確認
            tables = driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"Found {len(tables)} tables at depth {current_depth}")
            
            # テーブルの確認
            for table_idx, table in enumerate(tables):
                try:
                    # テーブルの構造を確認
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if not rows:
                        logger.info(f"Table {table_idx} has no rows, skipping...")
                        continue
                    
                    # テーブルのHTMLをログに記録
                    table_html = table.get_attribute("outerHTML")
                    logger.info(f"Table {table_idx} HTML structure:")
                    logger.info("=" * 80)
                    logger.info(table_html)
                    logger.info("=" * 80)
                    
                    # ヘッダー行を確認
                    header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        logger.info(f"Table {table_idx} has no header cells, skipping...")
                        continue
                    
                    # ヘッダーテキストを取得
                    header_texts = [cell.text.strip() for cell in header_cells]
                    logger.info(f"Table {table_idx} headers: {header_texts}")
                    
                    # 必要なカラムがあるか確認
                    required_headers = ['日付', '時刻', 'コード', '会社名', '表題']
                    if all(header in header_texts for header in required_headers):
                        logger.info(f"Found target table at depth {current_depth}")
                        return table
                    
                except StaleElementReferenceException:
                    logger.error(f"Table {table_idx} became stale while checking")
                    continue
                except Exception as e:
                    logger.error(f"Error checking table {table_idx}: {str(e)}")
                    continue
            
            # このフレーム内のiframeを取得
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"Found {len(iframes)} iframes at depth {current_depth}")
            
            # 各iframeを確認
            for idx, iframe in enumerate(iframes):
                try:
                    # iframeの属性を確認
                    iframe_attrs = {
                        'id': iframe.get_attribute('id'),
                        'name': iframe.get_attribute('name'),
                        'src': iframe.get_attribute('src')
                    }
                    logger.info(f"Checking iframe {idx} at depth {current_depth}:")
                    logger.info(json.dumps(iframe_attrs, ensure_ascii=False, indent=2))
                    
                    # iframeに切り替え
                    driver.switch_to.frame(iframe)
                    logger.info(f"Switched to iframe {idx} at depth {current_depth}")
                    
                    # 再帰的に探索
                    result = find_result_table(driver, max_attempts=1, wait_time=wait_time, current_depth=current_depth + 1)
                    if result:
                        return result
                    
                    # 目的のテーブルが見つからなければ親フレームに戻る
                    driver.switch_to.parent_frame()
                    logger.info(f"Switched back to parent frame from depth {current_depth + 1}")
                    
                except StaleElementReferenceException:
                    logger.error(f"Iframe {idx} became stale while checking")
                    continue
                except Exception as e:
                    logger.error(f"Error checking iframe {idx}: {str(e)}")
                    # エラーが発生した場合は最上位フレームに戻る
                    for _ in range(current_depth + 1):
                        try:
                            driver.switch_to.parent_frame()
                        except:
                            pass
                    continue
            
            if current_depth == 0:  # 最上位フレームの場合のみ待機
                logger.info(f"Target table not found in attempt {attempt + 1}, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                break  # 下位フレームの場合は待機せずに終了
            
        except Exception as e:
            logger.error(f"Error during attempt {attempt + 1}: {str(e)}")
            logger.error(traceback.format_exc())
            if attempt < max_attempts - 1 and current_depth == 0:
                time.sleep(wait_time)
                continue
            else:
                # エラーが発生した場合は最上位フレームに戻る
                for _ in range(current_depth + 1):
                    try:
                        driver.switch_to.parent_frame()
                    except:
                        pass
                break
    
    if current_depth == 0:
        logger.error("Failed to find result table after all attempts")
    return None

def analyze_table_data(driver):
    """テーブルデータの解析"""
    logger.info("\n=== テーブルデータの解析開始 ===")
    
    try:
        # 現在のページの状態を保存
        save_debug_info(driver, "before_analysis")
        
        # 検索結果のテーブルを探す
        table = find_result_table(driver, max_attempts=10, wait_time=5)
        if not table:
            logger.error("Failed to find result table")
            return
        
        logger.info("Found result table")
        
        try:
            # テーブルのHTML構造を解析
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")
            logger.info("Table structure:")
            logger.info(soup.prettify())
            
            # 行を取得
            rows = table.find_elements(By.TAG_NAME, "tr")
            logger.info(f"\nFound {len(rows)} rows")
            
            # ヘッダー行の解析
            header_cells = rows[0].find_elements(By.TAG_NAME, "th") if rows else []
            if header_cells:
                header_info = {
                    'columns': [cell.text.strip() for cell in header_cells],
                    'html': [cell.get_attribute('outerHTML') for cell in header_cells]
                }
                logger.info(f"\nHeader info:")
                logger.info(json.dumps(header_info, ensure_ascii=False, indent=2))
            
            # データ行の解析
            for row_idx, row in enumerate(rows[1:], 1):  # ヘッダーをスキップ
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    # 行データを収集
                    row_data = {
                        'index': row_idx,
                        'cells': []
                    }
                    
                    for cell_idx, cell in enumerate(cells):
                        cell_info = {
                            'index': cell_idx,
                            'text': cell.text.strip(),
                            'class': cell.get_attribute('class'),
                            'html': cell.get_attribute('outerHTML')
                        }
                        
                        # リンクの確認
                        links = cell.find_elements(By.TAG_NAME, "a")
                        if links:
                            cell_info['links'] = []
                            for link in links:
                                link_info = {
                                    'text': link.text.strip(),
                                    'href': link.get_attribute('href'),
                                    'onclick': link.get_attribute('onclick'),
                                    'target': link.get_attribute('target'),
                                    'html': link.get_attribute('outerHTML')
                                }
                                cell_info['links'].append(link_info)
                        
                        row_data['cells'].append(cell_info)
                    
                    # 行データを構造化
                    if len(row_data['cells']) >= 5:  # 必要なカラムがある場合
                        structured_data = {
                            'date': row_data['cells'][0]['text'],
                            'time': row_data['cells'][1]['text'],
                            'code': row_data['cells'][2]['text'],
                            'company': row_data['cells'][3]['text'],
                            'title': row_data['cells'][4]['text'],
                            'pdf_links': []
                        }
                        
                        # PDFリンクの確認（全てのセルをチェック）
                        for cell in row_data['cells']:
                            if 'links' in cell:
                                for link in cell['links']:
                                    href = link.get('href', '')
                                    text = link.get('text', '')
                                    if 'pdf' in href.lower() or '決算説明資料' in text:
                                        pdf_info = {
                                            'url': href,
                                            'text': text,
                                            'cell_index': cell['index'],
                                            'html': link['html']
                                        }
                                        structured_data['pdf_links'].append(pdf_info)
                        
                        logger.info(f"\n=== Row {row_idx} Data ===")
                        logger.info(json.dumps(structured_data, ensure_ascii=False, indent=2))
                        
                        if structured_data['pdf_links']:
                            logger.info(f"\nFound {len(structured_data['pdf_links'])} PDF links in row {row_idx}")
                            for pdf_link in structured_data['pdf_links']:
                                logger.info(f"PDF Link: {pdf_link['url']}")
                                logger.info(f"Link Text: {pdf_link['text']}")
                                logger.info(f"HTML: {pdf_link['html']}")
                
                except StaleElementReferenceException:
                    logger.error(f"行 {row_idx} の解析中に要素が古くなりました")
                    continue
                except Exception as e:
                    logger.error(f"行 {row_idx} の解析中にエラー: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"テーブルの解析中にエラー: {str(e)}")
            logger.error(traceback.format_exc())
            save_debug_info(driver, "analysis_error")
    
    except Exception as e:
        logger.error(f"テーブルの解析中にエラー: {str(e)}")
        logger.error(traceback.format_exc())
        save_debug_info(driver, "analysis_error")

def run_tdnet_browser():
    # Chromeオプションの設定
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja')
    
    # ブラウザを起動
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # メインページにアクセス
        logger.info("=== メインページアクセス ===")
        driver.get("https://www.release.tdnet.info/index.html")
        time.sleep(2)
        
        # 検索フォームのiframeに切り替え
        logger.info("検索フォームのiframeに切り替え")
        iframe = wait_for_element(driver, By.TAG_NAME, "iframe")
        if not iframe:
            logger.error("Failed to find search form iframe")
            return
        
        driver.switch_to.frame(iframe)
        logger.info("検索フォームのiframeに切り替え完了")
        
        # 開始日の選択
        start_date_select = Select(driver.find_element(By.NAME, "t0"))
        start_date_options = start_date_select.options
        logger.info(f"開始日の選択肢数: {len(start_date_options)}")
        
        # 最も古い日付（最小のvalue）を探す
        min_value = None
        min_index = None
        for i, option in enumerate(start_date_options):
            value = option.get_attribute('value')
            text = option.text
            logger.info(f"Option {i}: value: {value}, text: {text}")
            
            if value:  # 空でないvalueのみ処理
                try:
                    date_value = int(value)  # 数値として比較
                    if min_value is None or date_value < min_value:
                        min_value = date_value
                        min_index = i
                except ValueError:
                    continue
        
        if min_index is not None:
            # 最も古い日付を選択
            start_date_select.select_by_index(min_index)
            selected_option = start_date_select.first_selected_option
            logger.info(f"選択した開始日: value={selected_option.get_attribute('value')}, text={selected_option.text}")
        
        # 検索フォームを探す
        search_input = wait_for_element(driver, By.ID, "freewordtxt")
        if not search_input:
            logger.error("Failed to find search input")
            return
        
        # 検索キーワードを入力
        search_input.clear()
        search_input.send_keys("決算説明資料")
        logger.info("検索キーワード入力完了")
        
        # 検索ボタンをクリック
        search_button = wait_for_element(driver, By.CSS_SELECTOR, "#searchbtn > img")
        if not search_button:
            logger.error("Failed to find search button")
            return
        
        search_button.click()
        logger.info("検索ボタンクリック完了")
        time.sleep(5)  # 検索処理の完了を待機（時間を延長）
        
        # メインフレームに戻る
        driver.switch_to.default_content()
        logger.info("Switched back to main frame")
        
        # テーブルデータの解析
        analyze_table_data(driver)
        
        logger.info("処理が完了しました")
        input("Press Enter to close the browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tdnet_browser()
