import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);

  const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ??
    (import.meta.env.DEV ? 'http://localhost:8001/api/v1' : '/api/v1');

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      setUser({ email: 'admin@admin' });
    } else {
      localStorage.removeItem('token');
      setUser(null);
    }
  }, [token]);

  const login = async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const loginUrl = `${API_BASE_URL.replace(/\/api\/v1\/?$/, '')}/api/v1/auth/login`;
    
    const response = await fetch(loginUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Falha na autenticação');
    }

    const data = await response.json();
    setToken(data.access_token);
    return data;
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
