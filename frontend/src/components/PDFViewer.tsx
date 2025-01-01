import React from 'react';

interface PDFViewerProps {
  url: string;
}

export default function PDFViewer({ url }: PDFViewerProps) {
  return (
    <iframe
      src={url}
      className="w-full h-full border-0"
      title="PDF Viewer"
    />
  );
}
