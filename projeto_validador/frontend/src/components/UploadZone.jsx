import { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { preflightApi } from '../services/api';

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
const ALLOWED_TYPES = ['application/pdf'];

const UploadZone = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);

  const validateFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return false;
    
    if (!ALLOWED_TYPES.includes(selectedFile.type) && !selectedFile.name.endsWith('.pdf')) {
      setError('Apenas arquivos PDF são aceitos para validação gráfica.');
      return false;
    }
    
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError('O arquivo excede o limite de 500MB.');
      return false;
    }
    
    return true;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        startUpload(droppedFile);
      }
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        startUpload(selectedFile);
      }
    }
  };

  const formatApiError = (err) => {
    const d = err?.response?.data?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) {
      return d
        .map((x) => (typeof x?.msg === 'string' ? x.msg : JSON.stringify(x)))
        .join(' · ');
    }
    if (d && typeof d === 'object') return d.message || JSON.stringify(d);
    return err?.message || 'Falha no upload';
  };

  const startUpload = async (fileToUpload) => {
    setUploading(true);
    setProgress(0);

    try {
      const data = await preflightApi.uploadPdf(fileToUpload, {
        onUploadProgress: (pct) => setProgress(Math.min(99, pct)),
      });
      setProgress(100);
      setTimeout(() => {
        onUploadSuccess(data.job_id);
      }, 500);
    } catch (err) {
      setError(formatApiError(err));
      setUploading(false);
      setFile(null);
    }
  };

  return (
    <div className="upload-container">
      <AnimatePresence mode="wait">
        {!uploading ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            className={`dropzone glass-panel ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current.click()}
          >
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              accept=".pdf"
              onChange={handleChange}
            />
            
            <div className="dropzone-content">
              <div className="upload-icon-wrapper">
                 <Upload className="upload-icon" />
                 <div className="icon-glow" />
              </div>
              <h3>Arraste seu PDF aqui</h3>
              <p>ou clique para selecionar do seu computador</p>
              
              <div className="upload-constraints">
                 <span>PDF</span>
                 <span className="dot"></span>
                 <span>Máx 500MB</span>
              </div>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} 
                animate={{ opacity: 1, y: 0 }}
                className="upload-error"
                onClick={(e) => e.stopPropagation()}
              >
                <AlertCircle size={16} />
                {error}
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="upload-progress-box glass-panel"
          >
             <div className="uploading-header">
                <FileText className="file-icon" />
                <div className="file-info">
                   <span className="filename">{file?.name}</span>
                   <span className="filesize">{(file?.size / (1024 * 1024)).toFixed(1)} MB</span>
                </div>
                <Loader2 className="animate-spin text-primary" size={20} />
             </div>
             
             <div className="progress-container">
                <div className="progress-meta">
                   <span>{progress < 100 ? 'Fazendo upload...' : 'Enviado — iniciando análise...'}</span>
                   <span>{progress}%</span>
                </div>
                <div className="progress-bar-bg">
                   <motion.div 
                     className="progress-bar-fill"
                     initial={{ width: 0 }}
                     animate={{ width: `${progress}%` }}
                     transition={{ duration: 0.3 }}
                   />
                </div>
             </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx>{`
        .upload-container {
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }
        .dropzone {
          height: 300px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border: 2px dashed rgba(255,255,255,0.1);
          border-radius: 16px;
          cursor: pointer;
          transition: all 0.3s var(--ease-out);
          position: relative;
          background: #11141d;
        }
        .dropzone:hover, .dropzone.drag-active {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.05);
          transform: translateY(-4px);
        }
        .hidden { display: none; }
        
        .upload-icon-wrapper {
          position: relative;
          margin-bottom: 24px;
          display: flex;
          justify-content: center;
        }
        .upload-icon {
          width: 48px;
          height: 48px;
          color: #3b82f6;
          position: relative;
          z-index: 2;
        }
        .icon-glow {
          position: absolute;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          width: 80px; height: 80px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%);
          z-index: 1;
        }
        
        .dropzone-content { text-align: center; }
        .dropzone h3 { font-size: 20px; font-weight: 600; margin-bottom: 8px; color: white; }
        .dropzone p { color: #94a3b8; font-size: 14px; }
        
        .upload-constraints {
          margin-top: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          font-size: 11px;
          font-weight: 700;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .dot { width: 4px; height: 4px; border-radius: 50%; background: currentColor; opacity: 0.3; }
        
        .upload-error {
          position: absolute;
          bottom: -40px;
          left: 0; right: 0;
          padding: 10px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 8px;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
        }
        
        .upload-progress-box {
          padding: 32px;
          background: #11141d;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 16px;
        }
        .uploading-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 32px;
        }
        .file-icon { color: #94a3b8; }
        .file-info { flex: 1; display: flex; flex-direction: column; }
        .filename { font-size: 15px; font-weight: 600; color: white; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .filesize { font-size: 12px; color: #64748b; }
        
        .progress-container { width: 100%; }
        .progress-meta { 
          display: flex; justify-content: space-between; 
          font-size: 12px; font-weight: 600; color: #94a3b8;
          margin-bottom: 12px;
        }
        .progress-bar-bg {
          height: 6px;
          background: rgba(255,255,255,0.05);
          border-radius: 3px;
          overflow: hidden;
        }
        .progress-bar-fill {
          height: 100%;
          background: #3b82f6;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
        }
      `}</style>
    </div>
  );
};

export default UploadZone;
