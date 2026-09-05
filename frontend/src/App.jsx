import React, { useState, useEffect } from 'react';
import AppLayout from './components/AppLayout';
import OverviewPage from './pages/OverviewPage';
import MyAppliancesPage from './pages/MyAppliancesPage';
import RepairIssuesPage from './pages/RepairIssuesPage';
import AIInvestigationPage from './pages/AIInvestigationPage';
import './App.css';

function App() {
  // Read initial tab from URL hash if available
  const getInitialTab = () => {
    const hash = window.location.hash.replace('#', '');
    if (['overview', 'appliances', 'issues', 'investigation'].includes(hash)) {
      return hash;
    }
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [navParams, setNavParams] = useState({});

  // Sync state with URL hash
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['overview', 'appliances', 'issues', 'investigation'].includes(hash)) {
        setActiveTab(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleSelectTab = (tabId) => {
    setActiveTab(tabId);
    setNavParams({});
    window.location.hash = tabId;
  };

  const handleNavigate = (tabId, params = {}) => {
    setActiveTab(tabId);
    setNavParams(params);
    window.location.hash = tabId;
  };

  return (
    <AppLayout activeTab={activeTab} onSelectTab={handleSelectTab}>
      {activeTab === 'overview' && (
        <OverviewPage onNavigate={handleNavigate} />
      )}
      {activeTab === 'appliances' && (
        <MyAppliancesPage onNavigate={handleNavigate} />
      )}
      {activeTab === 'issues' && (
        <RepairIssuesPage
          onNavigate={handleNavigate}
          filterApplianceId={navParams.applianceId}
        />
      )}
      {activeTab === 'investigation' && (
        <AIInvestigationPage
          initialApplianceId={navParams.applianceId}
          initialIssueId={navParams.issueId}
        />
      )}
    </AppLayout>
  );
}

export default App;
