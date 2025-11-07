import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { X, Download, Maximize2, Minimize2 } from 'lucide-react';

interface HTMLViewerProps {
  htmlContent: string;
  fileName: string;
  onClose: () => void;
}

const HTMLViewer: React.FC<HTMLViewerProps> = ({ htmlContent, fileName, onClose }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [processedHtml, setProcessedHtml] = useState('');

  useEffect(() => {
    // HTMLコンテンツを処理して表示用に最適化
    const processed = processHtmlContent(htmlContent);
    setProcessedHtml(processed);
  }, [htmlContent]);

  const processHtmlContent = (html: string): string => {
    // XBRL形式のHTMLを処理
    let processed = html;
    
    // XBRLのXML宣言を削除
    processed = processed.replace(/^<\?xml[^>]*\?>\s*/, '');
    
    // XBRLコメントを削除
    processed = processed.replace(/<!--[\s\S]*?-->/g, '');
    
    // XBRLの名前空間属性を削除（表示に不要）
    processed = processed.replace(/\s+xmlns[^=]*="[^"]*"/g, '');
    processed = processed.replace(/\s+xml[^=]*="[^"]*"/g, '');
    
    // XBRL形式のHTMLを標準HTMLに変換
    processed = processed.replace(/<html[^>]*>/g, '<html>');
    
    // XBRLのメタデータ要素を削除
    processed = processed.replace(/<ix:header[^>]*>[\s\S]*?<\/ix:header>/gi, '');
    processed = processed.replace(/<ix:hidden[^>]*>[\s\S]*?<\/ix:hidden>/gi, '');
    processed = processed.replace(/<ix:nonNumeric[^>]*>[\s\S]*?<\/ix:nonNumeric>/gi, '');
    processed = processed.replace(/<ix:nonFraction[^>]*>[\s\S]*?<\/ix:nonFraction>/gi, '');
    
    // XBRLの長いIDやメタデータ文字列を削除
    processed = processed.replace(/[A-Za-z0-9]{20,}/g, (match) => {
      // 長すぎる文字列（20文字以上）で、URLやIDのようなものを削除
      if (match.includes('http://') || match.includes('Member') || match.includes('gaap:') || match.includes('xbrl:')) {
        return '';
      }
      return match;
    });
    
    // XBRLの期間情報やID情報を削除
    processed = processed.replace(/\d{4}-\d{2}-\d{2}\d{4}-\d{2}-\d{2}/g, '');
    processed = processed.replace(/\d{10,}/g, ''); // 10桁以上の数字を削除
    
    // 外部リンクを新しいタブで開くように設定
    processed = processed.replace(/<a\s+href="([^"]*)"([^>]*)>/g, '<a href="$1" target="_blank" rel="noopener noreferrer"$2>');
    
    // XBRLの非表示要素を削除
    processed = processed.replace(/<[^>]*style="[^"]*display\s*:\s*none[^"]*"[^>]*>[\s\S]*?<\/[^>]*>/gi, '');
    processed = processed.replace(/<[^>]*style="[^"]*visibility\s*:\s*hidden[^"]*"[^>]*>[\s\S]*?<\/[^>]*>/gi, '');
    
    // XBRLの非表示クラスを持つ要素を削除
    processed = processed.replace(/<[^>]*class="[^"]*hidden[^"]*"[^>]*>[\s\S]*?<\/[^>]*>/gi, '');
    
    // 空のdivやspanを削除
    processed = processed.replace(/<div[^>]*>\s*<\/div>/gi, '');
    processed = processed.replace(/<span[^>]*>\s*<\/span>/gi, '');
    
    // 不要な空白行を削除
    processed = processed.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    // 長い文字列の連結を削除（XBRLのメタデータ）
    processed = processed.replace(/[A-Za-z0-9]{50,}/g, '');
    
    // XBRLの特定のパターンを削除
    processed = processed.replace(/[A-Za-z0-9]{4}FY[A-Za-z0-9]{10,}/g, ''); // 2024FY...パターン
    processed = processed.replace(/http:\/\/[A-Za-z0-9\.\/\#\:]+/g, ''); // URLパターン
    processed = processed.replace(/[A-Za-z0-9]{4}-\d{2}-\d{2}[A-Za-z0-9]{4}-\d{2}-\d{2}/g, ''); // 日付連結パターン
    processed = processed.replace(/[A-Za-z0-9]{10,}Member/g, ''); // Memberパターン
    processed = processed.replace(/[A-Za-z0-9]{10,}gaap:/g, ''); // gaap:パターン
    processed = processed.replace(/[A-Za-z0-9]{10,}xbrl:/g, ''); // xbrl:パターン
    processed = processed.replace(/[A-Za-z0-9]{10,}iso4217:/g, ''); // iso4217:パターン
    processed = processed.replace(/[A-Za-z0-9]{10,}country:/g, ''); // country:パターン
    
    // 複数の空白を単一の空白に変換
    processed = processed.replace(/\s+/g, ' ');
    
    // 空の行を削除
    processed = processed.replace(/^\s*$/gm, '');
    
    // 基本的なスタイリングを追加
    const style = `
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 100%;
          margin: 0;
          padding: 20px;
          background-color: #fff;
        }
        
        h1, h2, h3, h4, h5, h6 {
          color: #2c3e50;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
        }
        
        h1 { font-size: 1.8em; border-bottom: 2px solid #3498db; padding-bottom: 0.5em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #bdc3c7; padding-bottom: 0.3em; }
        h3 { font-size: 1.3em; }
        
        p { margin-bottom: 1em; text-align: justify; }
        
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 1em 0;
          font-size: 0.9em;
        }
        
        th, td {
          border: 1px solid #bdc3c7;
          padding: 8px;
          text-align: left;
          vertical-align: top;
        }
        
        th {
          background-color: #ecf0f1;
          font-weight: bold;
        }
        
        tr:nth-child(even) {
          background-color: #f8f9fa;
        }
        
        .page-break {
          page-break-before: always;
        }
        
        .no-break {
          page-break-inside: avoid;
        }
        
        .long-text {
          word-wrap: break-word;
          overflow-wrap: break-word;
        }
        
        .number {
          text-align: right;
        }
        
        .important {
          color: #e74c3c;
          font-weight: bold;
        }
        
        .highlight {
          background-color: #fff3cd;
          padding: 2px 4px;
          border-radius: 3px;
        }
        
        /* XBRL特有のスタイル */
        [style*="display:none"] {
          display: none !important;
        }
        
        /* XBRL要素の非表示 */
        .xbrl-hidden,
        [class*="xbrl"][style*="display:none"],
        [id*="xbrl"][style*="display:none"],
        ix\\:header,
        ix\\:hidden,
        ix\\:nonNumeric,
        ix\\:nonFraction {
          display: none !important;
        }
        
        /* XBRLのメタデータ要素を非表示 */
        [id*="Member"],
        [id*="gaap:"],
        [id*="xbrl:"],
        [id*="iso4217:"],
        [id*="country:"] {
          display: none !important;
        }
        
        /* XBRLテーブルのスタイル改善 */
        .xbrl-table,
        table[class*="xbrl"] {
          border-collapse: collapse;
          width: 100%;
          margin: 1em 0;
        }
        
        /* XBRLセルのスタイル */
        .xbrl-cell,
        td[class*="xbrl"] {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        
        /* 数値の右寄せ */
        .xbrl-numeric,
        [class*="numeric"] {
          text-align: right;
        }
        
        /* ヘッダーのスタイル */
        .xbrl-header,
        th[class*="xbrl"] {
          background-color: #f5f5f5;
          font-weight: bold;
        }
        
        /* XBRL文書の全体的な改善 */
        .xbrl-document {
          max-width: 100%;
          overflow-x: auto;
        }
        
        /* 財務データテーブルの改善 */
        .financial-table,
        table[class*="financial"] {
          border: 2px solid #333;
          margin: 2em 0;
        }
        
        .financial-table th,
        table[class*="financial"] th {
          background-color: #2c3e50;
          color: white;
          padding: 12px;
          font-weight: bold;
        }
        
        .financial-table td,
        table[class*="financial"] td {
          padding: 10px;
          border-bottom: 1px solid #ddd;
        }
        
        /* 数値の表示改善 */
        .monetary,
        [class*="monetary"] {
          text-align: right;
          font-family: 'Courier New', monospace;
        }
        
        /* セクション見出しの改善 */
        .section-title,
        h1, h2, h3 {
          border-left: 4px solid #3498db;
          padding-left: 10px;
          margin-top: 2em;
        }
        
        /* レスポンシブ対応 */
        @media (max-width: 768px) {
          body {
            padding: 10px;
            font-size: 14px;
          }
          
          table {
            font-size: 12px;
          }
          
          th, td {
            padding: 4px;
          }
        }
      </style>
    `;
    
    // HTMLにスタイルを挿入
    if (processed.includes('<head>')) {
      processed = processed.replace('<head>', `<head>${style}`);
    } else if (processed.includes('<html>')) {
      processed = processed.replace('<html>', `<html><head>${style}</head>`);
    } else {
      processed = `<html><head>${style}</head><body>${processed}</body></html>`;
    }
    
    return processed;
  };

  const handleDownload = () => {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4 ${isFullscreen ? 'p-0' : ''}`}>
      <Card className={`bg-white shadow-2xl ${isFullscreen ? 'w-full h-full max-w-none max-h-none' : 'w-full max-w-6xl max-h-[90vh]'}`}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
          <CardTitle className="text-lg font-semibold truncate flex-1 mr-4">
            {fileName}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="flex items-center space-x-1"
            >
              <Download className="h-4 w-4" />
              <span>ダウンロード</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={toggleFullscreen}
              className="flex items-center space-x-1"
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="flex items-center space-x-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className={`p-0 ${isFullscreen ? 'h-full' : 'max-h-[calc(90vh-120px)]'} overflow-auto`}>
          <iframe
            srcDoc={processedHtml}
            className="w-full h-full border-0"
            title={fileName}
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
            style={{
              minHeight: '600px',
              backgroundColor: '#fff'
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default HTMLViewer;
