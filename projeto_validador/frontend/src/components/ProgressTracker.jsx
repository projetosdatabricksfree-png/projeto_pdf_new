import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { preflightApi } from '../services/api';

const PIPELINE_STAGE = {
  QUEUED:     { label: 'Na fila',              hint: 'Aguardando disponibilidade dos agentes...' },
  ROUTING:    { label: 'Roteamento',           hint: 'Gerente classificando o produto...' },
  PROBING:    { label: 'Análise profunda',     hint: 'Especialista inspecionando a estrutura do PDF...' },
  PROCESSING: { label: 'Validação técnica',    hint: 'Operário executando os 9 checkers GWG...' },
  VALIDATING: { label: 'Gerando relatório',    hint: 'Validador consolidando o veredicto...' },
  COMPLETED:  { label: 'Concluído',            hint: 'Validação pré-flight finalizada.' },
  GOLD_DELIVERED: { label: 'Concluído (Gold)', hint: 'Arquivo corrigido automaticamente.' },
  GOLD_DELIVERED_WITH_WARNINGS: { label: 'Concluído (com avisos)', hint: 'Arquivo corrigido com ressalvas.' },
  GOLD_REJECTED: { label: 'Falha (Gold)', hint: 'Tentativa de correção automática falhou.' },
  FAILED:     { label: 'Falha',                hint: 'Erro na pipeline de validação.' },
};

const STATUS_ICON = {
  PENDING: '○',
  RUNNING: '⏳',
  OK: '✓',
  AVISO: '⚠',
  ERRO: '✕',
  TIMEOUT: '⏱',
  FAILED: '✕',
};

const STATUS_COLOR = {
  PENDING: 'var(--text-muted, #94a3b8)',
  RUNNING: 'var(--accent, #3b82f6)',
  OK: 'var(--success, #22c55e)',
  AVISO: 'var(--warning, #f59e0b)',
  ERRO: 'var(--danger, #ef4444)',
  TIMEOUT: 'var(--warning, #f59e0b)',
  FAILED: 'var(--danger, #ef4444)',
};

const ProgressTracker = ({ jobId, onComplete, onFailed }) => {
  const [state, setState] = useState({
    pipeline: 'QUEUED',
    board: null,
    finalStatus: null,
    timeLeft: null,
  });
  const interval = useRef();

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      try {
        const data = await preflightApi.getJobProgress(jobId);
        if (cancelled) return;

        const board = data.board;
        let timeLeft = null;
        if (board?.eta_seconds && board?.started_at) {
          const elapsed = (Date.now() / 1000) - board.started_at;
          timeLeft = Math.max(0, Math.round(board.eta_seconds - elapsed));
        }

        setState({
          pipeline: data.pipeline_status || 'QUEUED',
          board: board,
          finalStatus: data.final_status,
          timeLeft: timeLeft
        });

        if (
          data.pipeline_status === 'DONE' || 
          data.pipeline_status === 'COMPLETED' ||
          data.pipeline_status === 'GOLD_DELIVERED' ||
          data.pipeline_status === 'GOLD_DELIVERED_WITH_WARNINGS'
        ) {
          clearInterval(interval.current);
          try {
            const report = await preflightApi.getReport(jobId);
            if (!cancelled) setTimeout(() => onComplete(report), 400);
          } catch {
            if (!cancelled) {
              setTimeout(
                () => onComplete({
                  job_id: jobId,
                  status: data.final_status || 'UNKNOWN',
                  produto: 'Relatório indisponível',
                  detalhes_tecnicos: {},
                  resumo: 'O job terminou, mas o relatório ainda não pôde ser carregado.',
                }),
                400,
              );
            }
          }
          return;
        }
        if (data.pipeline_status === 'FAILED' || data.pipeline_status === 'GOLD_REJECTED') {
          clearInterval(interval.current);
          if (!cancelled && onFailed) {
            onFailed({
              jobId,
              message:
                'A validação falhou no servidor (fila de processamento ou timeout). Verifique os logs do worker Celery.',
            });
          }
        }
      } catch {
        // network blip — keep polling
      }
    };

    tick();
    interval.current = setInterval(tick, 800);

    return () => {
      cancelled = true;
      clearInterval(interval.current);
    };
  }, [jobId, onComplete, onFailed]);

  const pipeline = PIPELINE_STAGE[state.pipeline] || PIPELINE_STAGE.QUEUED;
  const board = state.board;
  const total = board?.total ?? 0;
  const done = board?.done ?? 0;
  const pct = total ? Math.round((done / total) * 100) : (
    { QUEUED: 5, ROUTING: 15, PROBING: 25, PROCESSING: 40, VALIDATING: 90, DONE: 100 }[state.pipeline] ?? 5
  );
  const currentIdx = board?.stages?.findIndex((s) => s.status === 'RUNNING') ?? -1;
  const currentLabel =
    currentIdx >= 0 ? board.stages[currentIdx].label : pipeline.hint;

  const formatTime = (s) => {
    if (s === null || s === undefined) return '';
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="progress-container surface" role="region" aria-label="Progresso da validação">
      <div className="progress-header">
        <div>
          <span className="badge badge-accent">Pipeline Multi-Agentes</span>
          <h2>{pipeline.label}</h2>
        </div>
        <div className="progress-meta" style={{ textAlign: 'right' }}>
          <div className="progress-percentage" aria-hidden="true" style={{ fontSize: '1.4em', fontWeight: 800 }}>
            {board ? `${done}/${total}` : `${pct}%`}
          </div>
          {state.timeLeft !== null && state.pipeline !== 'DONE' && (
            <div className="eta-timer" style={{ fontSize: '0.85em', opacity: 0.6, marginTop: '2px' }}>
              Tempo estimado: <strong>{formatTime(state.timeLeft)}</strong>
            </div>
          )}
        </div>
      </div>

      <div
        className="progress-bar-bg"
        style={{ margin: '16px 0 12px' }}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progresso: ${pct}%`}
      >
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      <p className="status-message" style={{ minHeight: '1.4em' }}>
        {state.pipeline === 'FAILED'
          ? `❌ Falha: ${pipeline.hint}`
          : board && currentIdx >= 0
            ? `Etapa ${currentIdx + 1} de ${total} — ${currentLabel}`
            : pipeline.hint}
      </p>

      {board && (
        <ul className="stage-board" style={{ listStyle: 'none', padding: 0, margin: '20px 0 0', display: 'grid', gap: '8px' }}>
          {board.stages.map((stage, i) => (
            <li
              key={stage.name}
              style={{
                display: 'grid',
                gridTemplateColumns: '28px 24px 1fr auto',
                gap: '12px',
                alignItems: 'start',
                padding: '12px',
                borderRadius: '10px',
                background: stage.status === 'RUNNING' ? 'rgba(59,130,246,0.08)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${stage.status === 'RUNNING' ? 'rgba(59,130,246,0.25)' : 'rgba(148,163,184,0.1)'}`,
                transition: 'all 0.3s ease'
              }}
            >
              <span style={{ opacity: 0.4, fontVariantNumeric: 'tabular-nums', marginTop: '2px' }}>{String(i + 1).padStart(2, '0')}</span>
              <span style={{ 
                color: STATUS_COLOR[stage.status] || STATUS_COLOR.PENDING, 
                fontWeight: 700, 
                fontSize: '1.1em',
                marginTop: '1px'
              }}>
                {STATUS_ICON[stage.status] || '○'}
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ 
                  opacity: stage.status === 'PENDING' ? 0.5 : 1,
                  fontWeight: stage.status === 'RUNNING' ? 600 : 400
                }}>
                  {stage.label}
                </span>
                {stage.log && (stage.status === 'RUNNING' || stage.status === 'TIMEOUT' || stage.status === 'FAILED') && (
                  <span style={{ fontSize: '0.78em', opacity: 0.5, fontStyle: 'italic' }}>
                    {stage.log}
                  </span>
                )}
              </div>
              <span style={{ fontVariantNumeric: 'tabular-nums', opacity: 0.6, fontSize: '0.85em', marginTop: '2px' }}>
                {stage.duration_ms ? `${(stage.duration_ms / 1000).toFixed(1)}s` : (stage.status === 'RUNNING' ? '...' : '')}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div aria-live="polite" className="sr-only">
        {`Progresso: ${done} de ${total} etapas. ${currentLabel}`}
      </div>
    </div>
  );
};

export default ProgressTracker;
