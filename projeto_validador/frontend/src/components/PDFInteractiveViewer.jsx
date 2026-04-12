import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ZoomIn, ZoomOut, Maximize, Eye, EyeOff, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const PDFInteractiveViewer = ({ fileUrl, goToPageRequest }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [zoom, setZoom] = useState(1.0);
  const [showOverlays, setShowOverlays] = useState(true);
  const [layers, setLayers] = useState({
    bleed: true,
    trim: true,
    safeArea: true
  });

  const onDocumentLoadSuccess = ({ numPages: n }) => {
    setNumPages(n);
  };

  useEffect(() => {
    if (!goToPageRequest || typeof goToPageRequest.page !== 'number') return;
    const target = goToPageRequest.page;
    const max = numPages && numPages > 0 ? numPages : target;
    const clamped = Math.min(Math.max(1, target), Math.max(1, max));
    const id = requestAnimationFrame(() => setPageNumber(clamped));
    return () => cancelAnimationFrame(id);
  }, [goToPageRequest, numPages]);

  return (
    <div className="pdf-viewer-container glass-panel">
      {/* Toolbar */}
      <div className="viewer-toolbar">
        <div className="toolbar-group">
          <button
            type="button"
            className="btn-icon"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
          >
            <ChevronLeft size={18} />
          </button>
          <span className="page-indicator">Página {pageNumber} de {numPages ?? '…'}</span>
          <button
            type="button"
            className="btn-icon"
            disabled={!numPages || pageNumber >= numPages}
            onClick={() =>
              setPageNumber((prev) => {
                const max = numPages ?? prev;
                return Math.min(prev + 1, Math.max(1, max));
              })
            }
          >
            <ChevronRight size={18} />
          </button>
        </div>

        <div className="toolbar-group">
          <button className="btn-icon" type="button" onClick={() => setZoom((z) => Math.max(z - 0.1, 0.5))} title="Reduzir zoom">
            <ZoomOut size={18} />
          </button>
          <span className="zoom-text">{Math.round(zoom * 100)}%</span>
          <button className="btn-icon" type="button" onClick={() => setZoom((z) => Math.min(z + 0.1, 3))} title="Aumentar zoom">
            <ZoomIn size={18} />
          </button>
          <button className="btn-icon" type="button" onClick={() => setZoom(1)} title="Zoom 100 % (ajustar leitura)">
            <Maximize size={18} />
          </button>
        </div>

        <div className="toolbar-group">
          <button
            type="button"
            className={`btn-toolbar ${showOverlays ? 'active' : ''}`}
            onClick={() => setShowOverlays(!showOverlays)}
          >
            {showOverlays ? <Eye size={16} /> : <EyeOff size={16} />}
            Guia Visual
          </button>
          
          <div className="layer-toggles">
             <label className="toggle-item" title="Linha de Sangria">
               <input type="checkbox" checked={layers.bleed} onChange={() => setLayers({...layers, bleed: !layers.bleed})} />
               <span className="color-dot bleed"></span> Sangria
             </label>
             <label className="toggle-item" title="Linha de Corte">
               <input type="checkbox" checked={layers.trim} onChange={() => setLayers({...layers, trim: !layers.trim})} />
               <span className="color-dot trim"></span> Corte
             </label>
             <label className="toggle-item" title="Margem de Segurança">
               <input type="checkbox" checked={layers.safeArea} onChange={() => setLayers({...layers, safeArea: !layers.safeArea})} />
               <span className="color-dot safe"></span> Segurança
             </label>
          </div>
        </div>
      </div>

      {/* Main Viewport */}
      <div className="viewer-viewport">
        <Document
          file={{ url: fileUrl, withCredentials: false }}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="loading-state"><Loader2 className="animate-spin" /> Carregando visualização...</div>}
        >
          <div className="page-wrapper" style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}>
            <Page 
              pageNumber={pageNumber} 
              renderTextLayer={false} 
              renderAnnotationLayer={true}
              className="pdf-page-render"
            />
            
            {/* Overlays */}
            {showOverlays && (
              <div className="overlay-container">
                {layers.bleed && <div className="box-overlay bleed" />}
                {layers.trim && <div className="box-overlay trim" />}
                {layers.safeArea && <div className="box-overlay safe" />}
              </div>
            )}
          </div>
        </Document>
      </div>

      <style jsx>{`
        .pdf-viewer-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          min-height: 600px;
          background: #0f1117;
          overflow: hidden;
        }
        .viewer-toolbar {
          padding: 12px 20px;
          background: #161922;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          z-index: 10;
        }
        .toolbar-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .btn-icon {
          background: transparent;
          border: none;
          color: #94a3b8;
          cursor: pointer;
          padding: 6px;
          border-radius: 6px;
          display: flex;
          transition: all 0.2s;
        }
        .btn-icon:hover {
          background: rgba(255,255,255,0.05);
          color: white;
        }
        .page-indicator, .zoom-text {
          font-size: 13px;
          font-weight: 500;
          color: #cbd5e1;
          min-width: 60px;
          text-align: center;
        }
        .viewer-viewport {
          flex: 1;
          overflow: auto;
          display: flex;
          justify-content: center;
          padding: 40px;
          background: #090b10;
          background-image: 
            radial-gradient(circle at 50% 50%, rgba(255,255,255,0.02) 1px, transparent 1px);
          background-size: 32px 32px;
        }
        .page-wrapper {
          position: relative;
          box-shadow: 0 10px 40px rgba(0,0,0,0.5);
          background: white;
          transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .overlay-container {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
          z-index: 5;
        }
        .box-overlay {
          position: absolute;
          border-width: 2px;
        }
        .box-overlay.trim {
          top: 0; left: 0; right: 0; bottom: 0;
          border: 1px solid #06d6a0;
          box-shadow: 0 0 0 1000px rgba(0,0,0,0.2);
        }
        .box-overlay.bleed {
          top: -3mm; left: -3mm; right: -3mm; bottom: -3mm;
          border: 1px dashed #ef4444;
        }
        .box-overlay.safe {
          top: 3mm; left: 3mm; right: 3mm; bottom: 3mm;
          border: 1px dotted #3b82f6;
        }
        .btn-toolbar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: #1e293b;
          border: 1px solid rgba(255,255,255,0.05);
          border-radius: 8px;
          color: #94a3b8;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
        }
        .btn-toolbar.active {
          background: #334155;
          color: white;
          border-color: #3b82f6;
        }
        .layer-toggles {
          display: flex;
          gap: 12px;
          padding-left: 12px;
          border-left: 1px solid rgba(255,255,255,0.1);
        }
        .toggle-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: #64748b;
          cursor: pointer;
        }
        .color-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .color-dot.bleed { background: #ef4444; }
        .color-dot.trim { background: #06d6a0; }
        .color-dot.safe { background: #3b82f6; }
      `}</style>
    </div>
  );
};

export default PDFInteractiveViewer;
