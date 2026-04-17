import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Mail, Eye, EyeOff, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || 'Credenciais inválidas. Verifique e-mail e senha.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root">
      {/* Background glows */}
      <div className="login-glow login-glow-1" aria-hidden="true" />
      <div className="login-glow login-glow-2" aria-hidden="true" />

      <motion.div
        className="login-card"
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Header */}
        <div className="login-header">
          <div className="login-logo">
            <ShieldCheck size={28} />
          </div>
          <span className="badge badge-accent" style={{ marginTop: '16px' }}>
            Acesso Restrito
          </span>
          <h1 className="login-title">
            Graphic<span className="gradient-text">Pro</span>
          </h1>
          <p className="login-subtitle">
            Sistema de validação pré-flight industrial
          </p>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <div className="login-field">
            <label className="login-label" htmlFor="email">
              E-mail
            </label>
            <div className="login-input-wrap">
              <Mail size={16} className="login-input-icon" aria-hidden="true" />
              <input
                id="email"
                type="email"
                className="login-input"
                placeholder="admin@admin"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                autoComplete="username"
                required
              />
            </div>
          </div>

          {/* Password */}
          <div className="login-field">
            <label className="login-label" htmlFor="password">
              Senha
            </label>
            <div className="login-input-wrap">
              <Lock size={16} className="login-input-icon" aria-hidden="true" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="login-input login-input-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="login-toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <motion.div
              className="login-error"
              role="alert"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.2 }}
            >
              <AlertCircle size={15} aria-hidden="true" />
              {error}
            </motion.div>
          )}

          {/* Submit */}
          <button
            type="submit"
            className="btn btn-primary login-submit"
            disabled={loading || !email || !password}
          >
            {loading ? (
              <>
                <span className="login-spinner" aria-hidden="true" />
                Verificando...
              </>
            ) : (
              'Entrar'
            )}
          </button>
        </form>

        {/* Footer */}
        <p className="login-footer">
          Graphic-Pro &copy; {new Date().getFullYear()} &mdash; uso interno
        </p>
      </motion.div>
    </div>
  );
}
