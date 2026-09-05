import React from 'react';
import './PageHeader.css';

export function PageHeader({ pretitle, title, subtitle, actions }) {
  return (
    <header className="page-header">
      <div className="page-header-content">
        {pretitle && <div className="page-header-pretitle">{pretitle}</div>}
        <h1 className="page-header-title">{title}</h1>
        {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </header>
  );
}

export default PageHeader;
