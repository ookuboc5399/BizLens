#!/usr/bin/env python3
"""
PDF変換サービス
"""

import io
import logging
import re
import tempfile
import os
from typing import Optional
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class PDFConverterService:
    def __init__(self):
        pass
    
    def html_to_pdf(self, html_content: str, filename: str = "document.pdf") -> Optional[bytes]:
        """HTMLコンテンツをPDFに変換（Playwright使用）"""
        try:
            logger.info(f"Converting HTML to PDF using Playwright: {filename}")
            
            # HTMLコンテンツをクリーンアップ
            cleaned_html = self._clean_html_content(html_content)
            
            # 完全なHTMLドキュメントを作成
            full_html = self._create_full_html_document(cleaned_html)
            
            # 一時ファイルにHTMLを保存
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(full_html)
                temp_html_path = temp_file.name
            
            try:
                # PlaywrightでPDFを生成
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # HTMLファイルを読み込み
                    page.goto(f"file://{temp_html_path}")
                    
                    # PDFを生成
                    pdf_bytes = page.pdf(
                        format='A4',
                        margin={
                            'top': '1cm',
                            'right': '1cm',
                            'bottom': '1cm',
                            'left': '1cm'
                        },
                        print_background=True,
                        prefer_css_page_size=True
                    )
                    
                    browser.close()
                
                logger.info(f"PDF conversion successful: {len(pdf_bytes)} bytes")
                return pdf_bytes
                
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error converting HTML to PDF: {str(e)}")
            logger.error(f"Traceback: {error_details}")
            return None
    
    def _create_full_html_document(self, html_content: str) -> str:
        """完全なHTMLドキュメントを作成"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEC EDGAR Document</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        h1 {{
            font-size: 18pt;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5em;
        }}
        
        h2 {{
            font-size: 16pt;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 14pt;
        }}
        
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            page-break-inside: avoid;
        }}
        
        th, td {{
            border: 1px solid #bdc3c7;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}
        
        th {{
            background-color: #ecf0f1;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        .no-break {{
            page-break-inside: avoid;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 2px solid #3498db;
        }}
        
        .footer {{
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid #bdc3c7;
            font-size: 9pt;
            color: #666;
        }}
        
        .long-text {{
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .number {{
            text-align: right;
        }}
        
        .important {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        @media print {{
            body {{
                margin: 0;
                padding: 15px;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .no-break {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
        """
    
    def _clean_html_content(self, html_content: str) -> str:
        """HTMLコンテンツをクリーンアップ"""
        # 基本的なクリーンアップ
        cleaned = html_content
        
        # 不要なタグや属性を削除
        # スクリプトタグを削除
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # スタイルタグを削除
        cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 不要な属性を削除
        cleaned = re.sub(r'\s+on\w+="[^"]*"', '', cleaned)
        
        return cleaned
    
    def create_pdf_with_metadata(self, html_content: str, company_name: str, document_name: str, 
                                filing_date: str = None, report_date: str = None) -> Optional[bytes]:
        """メタデータ付きのPDFを作成（Playwright使用）"""
        try:
            logger.info(f"Creating PDF with metadata for {company_name}")
            
            # ヘッダーとフッターを追加
            header_html = f"""
            <div class="header">
                <h1>{company_name}</h1>
                <h2>{document_name}</h2>
                {f'<p><strong>Filing Date:</strong> {filing_date}</p>' if filing_date else ''}
                {f'<p><strong>Report Date:</strong> {report_date}</p>' if report_date else ''}
                <p><strong>Source:</strong> SEC EDGAR Database</p>
                <p><strong>Generated on:</strong> {self._get_current_date()}</p>
            </div>
            """
            
            footer_html = f"""
            <div class="footer">
                <p>This document was generated from SEC EDGAR data for {company_name}.</p>
                <p>Original document: {document_name}</p>
                <p>Generated on: {self._get_current_date()}</p>
            </div>
            """
            
            # 完全なHTMLを作成
            full_html_content = f"""
            {header_html}
            {html_content}
            {footer_html}
            """
            
            return self.html_to_pdf(full_html_content, f"{company_name}_{document_name}.pdf")
            
        except Exception as e:
            logger.error(f"Error creating PDF with metadata: {str(e)}")
            return None
    
    def _get_current_date(self) -> str:
        """現在の日付を取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
