import React from 'react';
import './Header.css';

const TAB_TITLES = {
  overview: 'System Overview',
  appliances: 'My Appliances',
  issues: 'Repair Issues',
  investigation: 'AI Diagnostic Investigation',
};

export function Header({ activeTab, onToggleSidebar }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <button
          type="button"
          className="menu-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <nav className="header-breadcrumb" aria-label="Breadcrumb">
          <span>HomeRepair</span>
          <span className="breadcrumb-separator">/</span>
          <span className="breadcrumb-current">{TAB_TITLES[activeTab] || 'Dashboard'}</span>
        </nav>
      </div>

      <div className="header-right">
        <div className="property-selector">
          <svg className="property-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
          <span>Property:</span>
          <span className="property-name">Main Residence</span>
        </div>

        <div className="user-badge">
          <div className="user-avatar">DU</div>
          <span className="user-label">Demo Homeowner</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
