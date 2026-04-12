import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { preflightApi } from '../services/api';

const STAGE_MAP = {
  QUEUED: { stage: 'Na fila', progress: 5, message: 'Aguardando disponibilidade dos agentes...' },
  ROUTING: { stage: 'Roteamento', progress: 20, message: 'Agente Gerente classificando o produto...' },
  PROBING: { stage: 'Análise Profunda', progress: 35, message: 'Agente Especialista realizando probing estrutural...' },
  PROCESSING: { stage: 'Validação', progress: 55, message: 'Operário executando validações técnicas...' },
  VALIDATING: { stage: 'Geração do Relatório', progress: 80, message: 'Agente Validador gerando relatório...' },
  COMPLETED: { stage: 'Concluído', progress: 100, message: 'Validação pré-flight finalizada!' },
  DONE: { stage: 'Concluído', progress: 100, message: 'Validação pré-flight finalizada!' },
  FAILED: { stage: 'Falha', progress: 0, message: 'Erro na pipeline de validação.' },
};

const ProgressTracker = ({ jobId, onComplete }) => {
  const [status, setStatus] = useState({
    progress: 5,
    stage: 'Iniciando...',
    status: 'QUEUED',
    message: 'Preparando pipeline multi-agentes...',
  });
  const interval = useRef();

  useEffect(() => {
    let progressSim = 5;

    interval.current = setInterval(async () => {
      try {
        const data = await preflightApi.getJobStatus(jobId);
        const mapped = STAGE_MAP[data.status] || STAGE_MAP.QUEUED;

        // Simulated progress advancement between stages
        if (data.status === 'PROCESSING' || data.status === 'VALIDATING') {
          progressSim = Math.min(progressSim + 3, mapped.progress);
        } else {
          progressSim = mapped.progress;
        }

        setStatus({
          progress: progressSim,
          stage: mapped.stage,
          status: data.status,
          message: mapped.message,
          agent: data.agent,
          produto: data.produto_detectado,
        });

        if (data.status === 'COMPLETED' || data.status === 'DONE') {
          clearInterval(interval.current);
          try {
            const report = await preflightApi.getReport(jobId);
            setTimeout(() => onComplete(report), 600);
          } catch {
            setTimeout(() => onComplete({
              job_id: jobId,
              status: data.status,
              agent: data.agent,
              produto_detectado: data.produto_detectado,
            }), 600);
          }
        }
        if (data.status === 'FAILED') {
          clearInterval(interval.current);
        }
      } catch {
        // Keep trying on network blips
      }
    }, 2000);

    return () => clearInterval(interval.current);
  }, [jobId, onComplete]);

  return (
    <div className="progress-container surface" role="region" aria-label="Progresso da validação">
      <div className="progress-header">
        <div>
          <span className="badge badge-accent">Pipeline Multi-Agentes</span>
          <h2>{status.stage || 'Processando...'}</h2>
        </div>
        <div className="progress-percentage" aria-hidden="true">
          {status.progress}%
        </div>
      </div>

      <div
        className="progress-bar-bg"
        role="progressbar"
        aria-valuenow={status.progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progresso: ${status.progress}%`}
      >
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${status.progress}%` }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      <p className="status-message">
        {status.status === 'FAILED'
          ? `❌ Falha: ${status.message || 'Erro desconhecido'}`
          : status.message || 'Processando camadas do arquivo...'
        }
      </p>

      {status.agent && (
        <p className="status-message" style={{ marginTop: '4px', opacity: 0.7 }}>
          🤖 Agente ativo: <strong>{status.agent}</strong>
          {status.produto && <> — {status.produto}</>}
        </p>
      )}

      <div aria-live="polite" className="sr-only">
        {`Progresso: ${status.progress}%. Etapa atual: ${status.stage || 'processando'}`}
      </div>
    </div>
  );
};

export default ProgressTracker;
