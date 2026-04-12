import { useState } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  Clock,
  Bot,
  Layout,
  List,
  Download,
  ShieldCheck,
  RotateCcw,
  Printer,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PDFInteractiveViewer from './PDFInteractiveViewer';

/* ─── SVG Score Ring Component (Refined) ────────────────────────────────── */
const ScoreRing = ({ score, color, size = 100 }) => {
  const strokeWidth = 5;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="score-visual" style={{ width: size, height: size, position: 'relative' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle 
          cx={size / 2} cy={size / 2} r={radius} 
          stroke="rgba(255,255,255,0.05)" strokeWidth={strokeWidth} fill="none" 
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color} strokeWidth={strokeWidth} fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s var(--spring-easing)' }}
        />
      </svg>
      <div className="score-inner">
        <span className="score-num">{score}</span>
        <span className="score-pct">%</span>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   SENIOR PREFLIGHT DASHBOARD
   ═══════════════════════════════════════════════════════════════════════════ */
const ReportDashboard = ({ report, onReset }) => {
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [activeLayout, setActiveLayout] = useState('split'); // 'split' | 'list'
  const [selectedErrorId, setSelectedErrorId] = useState(null);
  const [pageJump, setPageJump] = useState({ page: 1, nonce: 0 });

  // Extract report data
  const {
    job_id,
    status = 'DESCONHECIDO',
    agente_processador = 'N/A',
    produto = 'N/A',
    tempo_processamento_ms = 0,
    detalhes_tecnicos = {},
    resumo = ''
  } = report;

  const validationItems = Object.entries(detalhes_tecnicos)
    .filter(([, val]) => val && typeof val === 'object' && 'status' in val)
    .map(([key, val]) => ({
      id: key,
      label: key.replace(/_/g, ' '),
      status: val.status || 'OK',
      code: val.error_code || val.codigo || key,
      value: val.value_found || val.valor || '',
      expected: val.value_expected || '',
      pages: Array.isArray(val.paginas) ? val.paginas : [],
    }));

  const totalChecks = validationItems.length || 1;
  const errorCount = validationItems.filter((v) => v.status === 'ERRO').length;
  const warningCount = validationItems.filter((v) => v.status === 'AVISO').length;
  const score = Math.max(
    0,
    Math.round(((totalChecks - errorCount - warningCount * 0.4) / totalChecks) * 100),
  );

  const getStatusConfig = () => {
    switch(status) {
      case 'APROVADO': return { color: '#10b981', label: 'Pronto para Impressão', icon: ShieldCheck };
      case 'APROVADO_COM_RESSALVAS': return { color: '#f59e0b', label: 'Aprovado com Avisos', icon: AlertTriangle };
      default: return { color: '#ef4444', label: 'Reprovado', icon: AlertTriangle };
    }
  };
  const statusConfig = getStatusConfig();

  const filteredItems = validationItems.filter(item => {
    if (filterSeverity === 'ALL') return true;
    return item.status === filterSeverity;
  });

  const fileUrl = `${window.location.origin}/api/v1/jobs/${job_id}/file`;

  return (
    <div className="preflight-dashboard">
      {/* ─── Top Header ───────────────────────────────────────────────────── */}
      <header className="preflight-header glass-panel">
        <div className="header-left">
          <button className="btn-back" onClick={onReset}>
            <ArrowLeft size={18} />
          </button>
          <div className="job-info">
            <h1>{produto}</h1>
            <div className="job-meta">
              <span className="id-tag">ID: {typeof job_id === 'string' ? job_id.slice(0, 8) : '—'}</span>
              <span className="dot"></span>
              <span className="agent-tag"><Bot size={12} /> {agente_processador}</span>
              <span className="dot"></span>
              <span className="time-tag"><Clock size={12} /> {tempo_processamento_ms}ms</span>
            </div>
          </div>
        </div>

        <div className="header-actions">
           <div className="layout-picker">
             <button className={activeLayout === 'split' ? 'active' : ''} onClick={() => setActiveLayout('split')}><Layout size={16}/></button>
             <button className={activeLayout === 'list' ? 'active' : ''} onClick={() => setActiveLayout('list')}><List size={16}/></button>
           </div>
           <button className="btn btn-outline"><Download size={16} /> Relatório PDF</button>
           <button className="btn btn-primary"><Printer size={16} /> Enviar p/ Impressão</button>
        </div>
      </header>

      <main className={`preflight-content ${activeLayout}`}>
        {/* ─── Left Panel: Diagnostics ────────────────────────────────────── */}
        <section className="diagnostics-panel">
          <div className="health-summary glass-panel">
            <ScoreRing score={score} color={statusConfig.color} />
            <div className="health-text">
              <h3 style={{ color: statusConfig.color }}>{statusConfig.label}</h3>
              <p>{resumo}</p>
            </div>
          </div>

          <div className="filters-row">
            <div className="filter-chips">
              <button 
                className={`chip ${filterSeverity === 'ALL' ? 'active' : ''}`} 
                onClick={() => setFilterSeverity('ALL')}
              >Tudo <span>{validationItems.length}</span></button>
              <button 
                className={`chip chip-error ${filterSeverity === 'ERRO' ? 'active' : ''}`}
                onClick={() => setFilterSeverity('ERRO')}
              >Erros <span>{errorCount}</span></button>
              <button 
                className={`chip chip-warning ${filterSeverity === 'AVISO' ? 'active' : ''}`}
                onClick={() => setFilterSeverity('AVISO')}
              >Avisos <span>{warningCount}</span></button>
              <button 
                className={`chip chip-ok ${filterSeverity === 'OK' ? 'active' : ''}`}
                onClick={() => setFilterSeverity('OK')}
              >OK <span>{totalChecks - errorCount - warningCount}</span></button>
            </div>
          </div>

          <div className="results-list">
            <AnimatePresence>
              {filteredItems.map(item => (
                <motion.div 
                  key={item.id}
                  layout
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`result-card ${selectedErrorId === item.id ? 'selected' : ''} ${item.status}`}
                  onClick={() => {
                    setSelectedErrorId(item.id);
                    const firstPage = item.pages?.[0];
                    if (firstPage != null && !Number.isNaN(Number(firstPage))) {
                      setPageJump((j) => ({
                        page: Number(firstPage),
                        nonce: j.nonce + 1,
                      }));
                    }
                  }}
                >
                  <div className="result-header">
                    <span className="result-label">{item.label}</span>
                    <span className="result-code">{item.code}</span>
                  </div>
                  
                  {(item.value || item.expected) && (
                    <div className="result-details">
                      {item.value && <div className="detail"><span>Encontrado:</span> {item.value}</div>}
                      {item.expected && <div className="detail"><span>Esperado:</span> {item.expected}</div>}
                    </div>
                  )}

                  {item.pages?.length > 0 && (
                    <div className="result-pages">
                       {item.pages.map(p => <span key={p} className="page-tag">Pág {p}</span>)}
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Decision Actions */}
          <div className="decision-footer glass-panel">
            <h4>Decisão Final</h4>
            <div className="decision-actions">
               <label className="checkbox-container">
                 <input type="checkbox" />
                 <span className="checkmark"></span>
                 Aprovar arquivo com ressalvas e assumir riscos
               </label>
               <div className="btn-group">
                 <button className="btn btn-outline" style={{flex: 1}} onClick={onReset}><RotateCcw size={16}/> Substituir Arquivo</button>
                 <button className="btn btn-primary" style={{flex: 1}} disabled={status === 'REPROVADO'}>Aprovar para Produção</button>
               </div>
            </div>
          </div>
        </section>

        {/* ─── Right Panel: Previewer ─────────────────────────────────────── */}
        {activeLayout === 'split' && (
          <section className="previewer-panel">
             <PDFInteractiveViewer fileUrl={fileUrl} goToPageRequest={pageJump} />
          </section>
        )}
      </main>

      <style jsx>{`
        .preflight-dashboard {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-height: 100vh;
          gap: 20px;
          padding: 20px;
          background: #0a0b10;
        }
        .preflight-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          border-radius: 16px;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 20px;
        }
        .btn-back {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: white;
          width: 40px;
          height: 40px;
          border-radius: 12px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .job-info h1 {
          font-size: 20px;
          margin-bottom: 4px;
        }
        .job-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 11px;
          color: #64748b;
          font-weight: 600;
        }
        .dot { width: 3px; height: 3px; background: #334155; border-radius: 50%; }
        
        .header-actions { display: flex; gap: 12px; align-items: center; }
        .layout-picker {
          display: flex;
          background: rgba(0,0,0,0.2);
          padding: 4px;
          border-radius: 10px;
          margin-right: 8px;
        }
        .layout-picker button {
          background: transparent;
          border: none;
          color: #475569;
          padding: 6px 10px;
          cursor: pointer;
          border-radius: 6px;
        }
        .layout-picker button.active { background: #334155; color: white; }

        .preflight-content {
          display: flex;
          gap: 20px;
          flex: 1;
          min-height: 0;
        }
        .diagnostics-panel {
          flex: 0 0 450px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          min-height: 0;
        }
        .previewer-panel {
          flex: 1;
          border-radius: 16px;
          overflow: hidden;
          background: #11141d;
        }

        .health-summary {
          display: flex;
          align-items: center;
          gap: 20px;
          padding: 24px;
        }
        .score-inner {
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Outfit';
        }
        .score-num { font-size: 28px; font-weight: 700; color: white; }
        .score-pct { font-size: 14px; color: #64748b; margin-top: 6px; }

        .health-text h3 { font-size: 18px; margin-bottom: 4px; }
        .health-text p { font-size: 13px; color: #94a3b8; }

        .filter-chips { display: flex; gap: 8px; }
        .chip {
          padding: 6px 14px;
          border-radius: 99px;
          border: 1px solid rgba(255,255,255,0.05);
          background: rgba(255,255,255,0.03);
          color: #94a3b8;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .chip span { color: #475569; margin-left: 6px; }
        .chip.active { background: white; color: black; border-color: white; }
        .chip.active span { color: rgba(0,0,0,0.5); }
        .chip-error.active { background: #ef4444; color: white; border-color: #ef4444; }
        .chip-warning.active { background: #f59e0b; color: white; border-color: #f59e0b; }

        .results-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding-right: 4px;
        }
        .result-card {
          padding: 16px;
          background: #161922;
          border: 1px solid rgba(255,255,255,0.05);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .result-card:hover { border-color: rgba(255,255,255,0.1); transform: translateX(2px); }
        .result-card.selected { border-color: #3b82f6; background: rgba(59, 130, 246, 0.05); }
        .result-card.ERRO { border-left: 4px solid #ef4444; }
        .result-card.AVISO { border-left: 4px solid #f59e0b; }
        .result-card.OK { border-left: 4px solid #10b981; }

        .result-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .result-label { font-size: 14px; font-weight: 600; color: #cbd5e1; }
        .result-code { font-size: 10px; color: #475569; font-family: monospace; }
        
        .result-details { font-size: 12px; color: #94a3b8; display: grid; gap: 4px; }
        .detail span { color: #475569; font-weight: 600; }

        .page-tag {
          display: inline-block;
          margin-top: 10px;
          padding: 2px 8px;
          background: rgba(255,255,255,0.05);
          color: #64748b;
          font-size: 10px;
          border-radius: 4px;
          font-weight: 700;
        }

        .decision-footer {
          margin-top: auto;
          padding: 24px;
          border-radius: 16px;
        }
        .decision-footer h4 { font-size: 16px; margin-bottom: 16px; }
        .checkbox-container {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 13px;
          color: #94a3b8;
          cursor: pointer;
          margin-bottom: 20px;
        }
        .btn-group { display: flex; gap: 12px; }
      `}</style>
    </div>
  );
};

export default ReportDashboard;
