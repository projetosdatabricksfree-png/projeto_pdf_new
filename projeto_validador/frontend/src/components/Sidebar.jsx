import { LayoutDashboard, ChevronRight } from 'lucide-react';

const Sidebar = ({ activeView, setView, onReset, isOpen, onToggle }) => {
  return (
    <nav
      className={`sidebar ${isOpen ? 'expanded' : ''}`}
      aria-label="Menu principal"
      onMouseEnter={onToggle ? () => !isOpen && onToggle() : undefined}
      onMouseLeave={onToggle ? () => isOpen && onToggle() : undefined}
    >
      {/* Logo */}
      <div className="sidebar-logo">
        <img src="/logo.png" alt="" className="nav-logo" aria-hidden="true" />
        <div className="logo-text-wrapper">
          <h1>PreFlight<span>Validator</span></h1>
          <span className="backend-tag python">Multi-Agente</span>
        </div>
      </div>

      {/* Toggle Button */}
      <button
        className="sidebar-toggle"
        onClick={onToggle}
        aria-label={isOpen ? 'Recolher menu' : 'Expandir menu'}
        title={isOpen ? 'Recolher menu' : 'Expandir menu'}
      >
        <ChevronRight
          size={14}
          style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 250ms ease' }}
        />
      </button>

      {/* Navigation Menu */}
      <div className="sidebar-menu" role="menubar" aria-label="Navegação principal">
        <button
          role="menuitem"
          className={`menu-item ${activeView === 'upload' ? 'active' : ''}`}
          onClick={() => { setView('upload'); if (onReset) onReset(); }}
          aria-current={activeView === 'upload' ? 'page' : undefined}
          title="Nova Validação"
        >
          <LayoutDashboard size={20} aria-hidden="true" />
          <span className="menu-item-label">Nova Validação</span>
        </button>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="user-snippet">
          <div className="user-avatar" aria-hidden="true">A</div>
          <div className="user-info">
            <span className="name">AlphaGraphics</span>
            <span className="email-text">Sistema Multi-Agentes</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;
