import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import './AppLayout.css';

export function AppLayout({ activeTab, onSelectTab, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="app-main-container">
        <Header
          activeTab={activeTab}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        />
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
