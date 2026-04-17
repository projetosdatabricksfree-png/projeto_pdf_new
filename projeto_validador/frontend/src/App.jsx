import { useState, Suspense, lazy, useCallback } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Sidebar from './components/Sidebar';
import UploadZone from './components/UploadZone';
import LoginPage from './components/LoginPage';
const ProgressTracker = lazy(() => import('./components/ProgressTracker'));
const ReportDashboard = lazy(() => import('./components/ReportDashboard'));

// Auth
import { useAuth } from './context/AuthContext';

// Styles
import './App.css';

function App() {
  const { isAuthenticated } = useAuth();
  const [view, setView] = useState('upload');
  const [phase, setPhase] = useState('upload');
  const [jobId, setJobId] = useState(null);
  const [report, setReport] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [jobPipelineError, setJobPipelineError] = useState(null);

  const handleJobComplete = useCallback((rep) => {
    setReport(rep);
    setPhase('report');
    setView('report');
    setJobPipelineError(null);
  }, []);

  const handleJobFailed = useCallback(({ message }) => {
    setJobPipelineError(message);
    setPhase('upload');
    setJobId(null);
  }, []);

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <>
      {/* Skip Navigation — Accessibility */}
      <a href="#main-content" className="skip-nav">
        Pular para o conteúdo principal
      </a>

      <div className="app-container">
        <Sidebar
          activeView={view}
          setView={setView}
          onReset={() => { setPhase('upload'); setReport(null); }}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        <div className={`main-wrapper ${sidebarOpen ? 'sidebar-open' : ''}`}>
          <main id="main-content" role="main" aria-label="Conteúdo principal">
            <AnimatePresence mode="wait">
              {view === 'upload' && (
                <motion.div
                  key="v-upload"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                >
                  {phase === 'upload' && (
                    <section className="section-hero" aria-label="Upload de arquivo">
                      {jobPipelineError && (
                        <div
                          className="pipeline-error-banner"
                          role="alert"
                        >
                          {jobPipelineError}
                        </div>
                      )}
                      <div className="hero-content">
                        <span className="badge badge-accent">Sistema Multi-Agentes</span>
                        <h1>
                          Validação pré-flight para{' '}
                          <span className="gradient-text">impressão profissional</span>
                        </h1>
                        <p>
                          Sistema de agentes especializados que valida seus arquivos com precisão industrial — cores CMYK, resolução, sangria, fontes e conformidade ISO 12647-2.
                        </p>
                        <ul className="features" aria-label="Recursos da validação">
                          <li className="feature">
                            <CheckCircle size={18} aria-hidden="true" />
                            5 agentes operários especializados
                          </li>
                          <li className="feature">
                            <CheckCircle size={18} aria-hidden="true" />
                            Roteamento geométrico inteligente
                          </li>
                          <li className="feature">
                            <CheckCircle size={18} aria-hidden="true" />
                            100% determinístico — sem LLM
                          </li>
                          <li className="feature">
                            <CheckCircle size={18} aria-hidden="true" />
                            Conformidade PDF/X-1a e ISO 12647-2
                          </li>
                        </ul>
                      </div>
                      <UploadZone
                        onUploadSuccess={(id) => {
                          setJobPipelineError(null);
                          setJobId(id);
                          setPhase('progress');
                        }}
                      />
                    </section>
                  )}
                  {phase === 'progress' && (
                    <section className="section-centered" aria-label="Progresso da validação">
                      <Suspense fallback={<div className="loading-spinner"><Loader2 className="animate-spin" /></div>}>
                        <ProgressTracker
                          jobId={jobId}
                          onComplete={handleJobComplete}
                          onFailed={handleJobFailed}
                        />
                      </Suspense>
                    </section>
                  )}
                </motion.div>
              )}

              {view === 'report' && report && (
                <motion.div
                  key="v-report"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <Suspense fallback={<div className="loading-spinner"><Loader2 className="animate-spin" /></div>}>
                    <ReportDashboard
                      report={report}
                      onReset={() => {
                        setView('upload');
                        setPhase('upload');
                        setReport(null);
                      }}
                    />
                  </Suspense>
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </div>
    </>
  );
}

export default App;
