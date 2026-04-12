import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, Activity, AlertCircle, Shield } from 'lucide-react';
import { preflightApi } from '../services/api';

const UploadZone = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const ALLOWED_TYPES = ['application/pdf', 'image/tiff', 'image/jpeg'];

  const handleFile = async (file) => {
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError('Formato inválido: envie um arquivo PDF, TIFF ou JPEG.');
      return;
    }
    setError(null);
    setIsUploading(true);
    try {
      const data = await preflightApi.uploadPdf(file);
      onUploadSuccess(data.job_id);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Falha no upload. Verifique sua conexão e tente novamente.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <motion.div
      className={`upload-zone surface ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !isUploading && fileInputRef.current.click()}
      role="button"
      tabIndex={0}
      aria-label="Área de upload — clique ou arraste um arquivo PDF"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          !isUploading && fileInputRef.current.click();
        }
      }}
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => handleFile(e.target.files[0])}
        style={{ display: 'none' }}
        accept=".pdf,.tiff,.tif,.jpeg,.jpg"
        aria-hidden="true"
      />

      <div className="upload-icon-container">
        {isUploading ? (
          <Activity className="animate-spin" size={48} style={{ color: 'var(--accent)' }} />
        ) : (
          <Upload size={48} />
        )}
      </div>

      <h3>{isUploading ? 'Enviando para os agentes...' : 'Arraste seu arquivo aqui'}</h3>
      <p>{isUploading ? 'Os agentes estão processando sua validação' : 'Clique ou solte o arquivo para iniciar a validação pré-flight'}</p>

      {!isUploading && (
        <div className="upload-footer">
          <Shield size={14} aria-hidden="true" />
          <span>PDF • TIFF • JPEG — Máximo 200 MB</span>
        </div>
      )}

      <div aria-live="polite" className="sr-only">
        {isUploading && 'Upload em andamento. Aguarde...'}
        {error && error}
      </div>

      {error && (
        <div className="error-message" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          {error}
        </div>
      )}
    </motion.div>
  );
};

export default UploadZone;
