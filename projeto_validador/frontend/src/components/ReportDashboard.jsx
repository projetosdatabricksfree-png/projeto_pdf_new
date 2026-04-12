import { useState } from 'react';
import { AlertTriangle, Filter, CheckCircle2, ArrowLeft, FileCheck, Clock, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/* ─── SVG Score Ring Component ──────────────────────────────────────────── */
const ScoreRing = ({ score, color, size = 80 }) => {
  const strokeWidth = 4;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="score-visual" style={{ width: size, height: size }}>
      <svg className="score-ring" width={size} height={size} aria-hidden="true">
        <circle className="score-ring-bg" cx={size / 2} cy={size / 2} r={radius} />
        <circle
          className="score-ring-fill"
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      <span className="score-num">{score}</span>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   REPORT DASHBOARD — Multi-Agent Version
   ═══════════════════════════════════════════════════════════════════════════ */
const ReportDashboard = ({ report, onReset }) => {
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  // Determine status from report
  const status = report?.status || 'DESCONHECIDO';
  const agent = report?.agente_processador || 'N/A';
  const produto = report?.produto || 'N/A';
  const processingTime = report?.tempo_processamento_ms || 0;

  // Get errors and warnings
  const erros = report?.erros || [];
  const avisos = report?.avisos || [];
  const validationResults = report?.detalhes_tecnicos || {};

  // Score based on results
  const totalChecks = Object.keys(validationResults).length || 1;
  const errorChecks = Object.values(validationResults).filter(v => v?.status === 'ERRO').length;
  const warningChecks = Object.values(validationResults).filter(v => v?.status === 'AVISO').length;
  const score = Math.max(0, Math.round(((totalChecks - errorChecks - warningChecks * 0.5) / totalChecks) * 100));

  const getScoreColor = () => {
    if (status === 'APROVADO') return '#06d6a0';
    if (status === 'APROVADO_COM_RESSALVAS') return '#f59e0b';
    return '#f43f5e';
  };

  const getScoreLabel = () => {
    if (status === 'APROVADO') return 'Aprovado para Impressão';
    if (status === 'APROVADO_COM_RESSALVAS') return 'Aprovado com Ressalvas';
    return 'Reprovado — Correções Necessárias';
  };

  const getStatusBadge = () => {
    if (status === 'APROVADO') return { bg: '#06d6a018', color: '#06d6a0', border: '#06d6a033', text: '✅ APROVADO' };
    if (status === 'APROVADO_COM_RESSALVAS') return { bg: '#f59e0b18', color: '#f59e0b', border: '#f59e0b33', text: '⚠️ COM RESSALVAS' };
    return { bg: '#f43f5e18', color: '#f43f5e', border: '#f43f5e33', text: '❌ REPROVADO' };
  };

  const badge = getStatusBadge();

  // Build validation items list
  const validationItems = Object.entries(validationResults).map(([key, value]) => ({
    id: key,
    codigo: value?.codigo || key,
    status: value?.status || 'OK',
    valor: value?.valor || value?.valor_encontrado || value?.detalhe || '',
    esperado: value?.valor_esperado || '',
    paginas: value?.paginas || [],
  }));

  const filteredItems = validationItems.filter(item => {
    if (filterSeverity === 'ALL') return true;
    if (filterSeverity === 'ERRO') return item.status === 'ERRO';
    if (filterSeverity === 'AVISO') return item.status === 'AVISO';
    if (filterSeverity === 'OK') return item.status === 'OK';
    return true;
  });

  return (
    <div className="dashboard" role="region" aria-label="Relatório de validação pré-flight">
      {/* Header */}
      <header className="dashboard-header surface">
        <div>
          <button className="back-link" onClick={onReset}>
            <ArrowLeft size={16} aria-hidden="true" />
            Nova Validação
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 className="dashboard-title">{produto}</h2>
            <div
              className="score-badge"
              style={{
                backgroundColor: badge.bg,
                color: badge.color,
                border: `1px solid ${badge.border}`,
              }}
            >
              {badge.text}
            </div>
          </div>
          <span className="dashboard-meta">
            <Bot size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Agente: {agent} • Tempo: {processingTime}ms
          </span>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="summary-grid">
        <motion.div
          className="summary-card surface score-card"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ScoreRing score={score} color={getScoreColor()} />
          <div className="score-info">
            <h4>Saúde do Arquivo</h4>
            <p>{getScoreLabel()}</p>
          </div>
        </motion.div>

        <motion.div
          className="summary-card surface critical"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="icon">
            <AlertTriangle size={24} aria-hidden="true" />
          </div>
          <div className="data">
            <span className="value">{erros.length}</span>
            <span className="label">Erros Críticos</span>
          </div>
        </motion.div>

        <motion.div
          className="summary-card surface warning"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="icon">
            <AlertTriangle size={24} aria-hidden="true" />
          </div>
          <div className="data">
            <span className="value">{avisos.length}</span>
            <span className="label">Avisos</span>
          </div>
        </motion.div>

        <motion.div
          className="summary-card surface info"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <div className="icon">
            <Clock size={24} aria-hidden="true" />
          </div>
          <div className="data">
            <span className="value">{totalChecks}</span>
            <span className="label">Verificações</span>
          </div>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="filters-bar surface" role="toolbar" aria-label="Filtros de resultado">
        <div className="filter-label">
          <Filter size={16} aria-hidden="true" /> Filtrar:
        </div>
        <div className="filter-options" role="radiogroup" aria-label="Nível de resultado">
          {[
            { key: 'ALL', label: 'Tudo', count: validationItems.length },
            { key: 'ERRO', label: 'Erros', count: validationItems.filter(i => i.status === 'ERRO').length, className: 'critical' },
            { key: 'AVISO', label: 'Avisos', count: validationItems.filter(i => i.status === 'AVISO').length, className: 'warning' },
            { key: 'OK', label: 'OK', count: validationItems.filter(i => i.status === 'OK').length },
          ].map((filter) => (
            <button
              key={filter.key}
              role="radio"
              aria-checked={filterSeverity === filter.key}
              className={`filter-btn ${filter.className || ''} ${filterSeverity === filter.key ? 'active' : ''}`}
              onClick={() => setFilterSeverity(filter.key)}
            >
              {filter.label} ({filter.count})
            </button>
          ))}
        </div>
      </div>

      {/* Validation Results */}
      <div className="pages-list">
        <AnimatePresence>
          {filteredItems.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="empty-filter surface"
            >
              <CheckCircle2 size={48} aria-hidden="true" />
              <h3>Nenhum problema encontrado!</h3>
              <p>Mude o filtro ou seu arquivo está impecável.</p>
            </motion.div>
          ) : (
            filteredItems.map((item, idx) => (
              <motion.article
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ delay: idx * 0.04 }}
                key={item.id}
                className="page-card surface"
                aria-label={`${item.id} — ${item.status}`}
              >
                <div className="page-card-content">
                  <div className="page-errors-side" style={{ flex: 1 }}>
                    <h3>
                      <FileCheck size={16} style={{ marginRight: '8px', display: 'inline' }} />
                      {item.id.replace(/_/g, ' ')}
                    </h3>
                    <div className="errors-list">
                      <div className={`error-item ${item.status === 'ERRO' ? 'critical' : item.status === 'AVISO' ? 'warning' : 'info'}`} role="listitem">
                        <div className="error-body" style={{ flex: 1 }}>
                          <div className="error-header">
                            <div className="error-code">{item.codigo}</div>
                            <div className={`status-pill ${item.status === 'ERRO' ? 'FAILED' : item.status === 'AVISO' ? 'PROCESSING' : 'COMPLETED'}`}>
                              <span className="status-dot" aria-hidden="true" />
                              {item.status}
                            </div>
                          </div>
                          {item.valor && (
                            <div className="error-msg">
                              <strong>Encontrado:</strong> {item.valor}
                            </div>
                          )}
                          {item.esperado && (
                            <div className="error-msg" style={{ opacity: 0.7 }}>
                              <strong>Esperado:</strong> {item.esperado}
                            </div>
                          )}
                          {item.paginas?.length > 0 && (
                            <div className="error-msg" style={{ marginTop: '4px', opacity: 0.6 }}>
                              📄 Páginas afetadas: {item.paginas.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.article>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ReportDashboard;
