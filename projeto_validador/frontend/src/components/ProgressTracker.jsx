import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { preflightApi } from '../services/api';

const STAGE_MAP = {
  QUEUED: { stage: 'Na fila', progress: 5, message: 'Aguardando disponibilidade dos agentes...' },
  ROUTING: { stage: 'Roteamento', progress: 20, message: 'Agente Gerente classificando o produto...' },
  PROBING: { stage: 'Análise profunda', progress: 35, message: 'Agente Especialista analisando a estrutura do PDF...' },
  PROCESSING: { stage: 'Validação', progress: 55, message: 'Operário executando validações técnicas...' },
  VALIDATING: { stage: 'Geração do Relatório', progress: 80, message: 'Agente Validador gerando relatório...' },
  COMPLETED: { stage: 'Concluído', progress: 100, message: 'Validação pré-flight finalizada!' },
  DONE: { stage: 'Concluído', progress: 100, message: 'Validação pré-flight finalizada!' },
  FAILED: { stage: 'Falha', progress: 0, message: 'Erro na pipeline de validação.' },
};

const ProgressTracker = ({ jobId, onComplete, onFailed }) => {
  const [status, setStatus] = useState({
    progress: 5,
    stage: 'Iniciando...',
    status: 'QUEUED',
    message: 'Preparando pipeline multi-agentes...',
  });
  const interval = useRef();

  useEffect(() => {
    let progressSim = 5;
    let cancelled = false;

    const tick = async () => {
      try {
        const data = await preflightApi.getJobStatus(jobId);
        if (cancelled) return;

        const mapped = STAGE_MAP[data.status] || STAGE_MAP.QUEUED;

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

        if (data.status === 'DONE' || data.status === 'COMPLETED') {
          clearInterval(interval.current);
          try {
            const report = await preflightApi.getReport(jobId);
            if (!cancelled) setTimeout(() => onComplete(report), 400);
          } catch {
            if (!cancelled) {
              setTimeout(
                () =>
                  onComplete({
                    job_id: jobId,
                    status: data.final_status || 'UNKNOWN',
                    produto: 'Relatório indisponível',
                    detalhes_tecnicos: {},
                    resumo: 'O job terminou, mas o relatório ainda não pôde ser carregado. Tente atualizar.',
                  }),
                400,
              );
            }
          }
          return;
        }
        if (data.status === 'FAILED') {
          clearInterval(interval.current);
          if (!cancelled && onFailed) {
            onFailed({
              jobId,
              message:
                'A validação falhou no servidor (fila de processamento ou timeout). Tente de novo ou verifique se o worker Celery está em execução.',
            });
          }
        }
      } catch {
        // Keep trying on network blips
      }
    };

    tick();
    interval.current = setInterval(tick, 2000);

    return () => {
      cancelled = true;
      clearInterval(interval.current);
    };
  }, [jobId, onComplete, onFailed]);

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
