import React, { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import Metric from '../components/Metric';
import StatusBadge from '../components/StatusBadge';
import { ApplianceService, IssueService } from '../services/api';
import './OverviewPage.css';

export function OverviewPage({ onNavigate }) {
  const [appliances, setAppliances] = useState([]);
  const [allIssues, setAllIssues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        const apps = await ApplianceService.getAppliances();
        setAppliances(apps);
        
        let issues = [];
        for (const app of apps) {
          const appIssues = await IssueService.getApplianceIssues(app.id);
          issues = issues.concat(appIssues);
        }
        setAllIssues(issues);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  // Compute metrics
  const activeAppliancesCount = appliances.length;
  const openIssues = allIssues.filter(i => i.status === 'open' || i.status === 'reopened');
  const openIssuesCount = openIssues.length;
  const inProgressCount = allIssues.filter(i => i.status === 'repair_scheduled' || i.status === 'parts_ordered' || i.status === 'in_progress').length;
  
  const now = new Date();
  const upcomingExpiriesCount = appliances.filter(a => {
    if (!a.warranty_expiry) return false;
    const expiry = new Date(a.warranty_expiry);
    const diffDays = (expiry - now) / (1000 * 60 * 60 * 24);
    return diffDays > 0 && diffDays <= 30;
  }).length;

  const completedIssues = allIssues.filter(i => i.status === 'resolved' || i.repair_outcome).sort((a, b) => new Date(b.resolved_at || 0) - new Date(a.resolved_at || 0));

  // Compute attention items
  const attentionItems = [];
  openIssues.forEach(issue => {
    const app = appliances.find(a => a.id === issue.appliance_id);
    attentionItems.push({
      id: `issue-${issue.id}`,
      type: issue.severity === 'critical' ? 'issue_critical' : 'issue_warning',
      title: issue.title,
      description: issue.description || 'Action required to diagnose and resolve.',
      appliance: app ? app.name : 'Unknown',
      urgency: issue.severity === 'critical' ? 'Immediate Action' : 'Needs Diagnosis',
      actionText: 'Diagnose Problem',
      targetTab: 'appliances',
      applianceId: issue.appliance_id,
      issueId: issue.id
    });
  });

  return (
    <div className="overview-page">
      <PageHeader
        pretitle="Dashboard"
        title="Home Appliance Overview"
        subtitle="Operational health, warranty readiness, and active repair tracking across your registered household appliances."
        actions={
          <>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onNavigate('appliances')}
            >
              Manage Appliances
            </button>
          </>
        }
      />

      {loading ? (
        <div className="overview-loading">Loading dashboard data...</div>
      ) : (
        <>
          {/* Structured Metrics Grid */}
          <section className="overview-grid-metrics" aria-label="System Metrics">
            <Metric
              label="Active Appliances"
              value={activeAppliancesCount}
              subtitle="All systems monitored"
              icon={
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="4" y="2" width="16" height="20" rx="2" />
                  <line x1="4" y1="10" x2="20" y2="10" />
                </svg>
              }
            />
            <Metric
              label="Open Issues"
              value={openIssuesCount}
              subtitle="Requires troubleshooting"
              trend={openIssuesCount > 0 ? "Action Needed" : "All Clear"}
              trendType={openIssuesCount > 0 ? "warning" : "success"}
              icon={
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                </svg>
              }
            />
            <Metric
              label="Repairs in Progress"
              value={inProgressCount}
              subtitle="Awaiting parts/schedule"
              icon={
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              }
            />
            <Metric
              label="Upcoming Expiries"
              value={upcomingExpiriesCount}
              subtitle="Within 30 days"
              trend={upcomingExpiriesCount > 0 ? "Review Warranty" : "Up to Date"}
              trendType={upcomingExpiriesCount > 0 ? "warning" : "success"}
              icon={
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              }
            />
            <Metric
              label="Completed Repairs"
              value={completedIssues.length}
              subtitle="Completed service history"
              icon={
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              }
            />
          </section>

          {/* Need Attention Section */}
          {attentionItems.length > 0 && (
            <section className="attention-section">
              <div className="attention-header">
                <svg className="attention-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <h2 className="attention-title">Need Attention</h2>
                <span className="attention-badge-count">{attentionItems.length} items</span>
              </div>

              <div className="attention-list">
                {attentionItems.map((item) => (
                  <div
                    key={item.id}
                    className={`attention-card ${item.type === 'issue_critical' ? 'critical' : 'warning'}`}
                  >
                    <div className="attention-card-main">
                      <div className="attention-card-top">
                        <span className="attention-card-title">{item.title}</span>
                        <span className="attention-card-urgency">{item.urgency}</span>
                      </div>
                      <p className="attention-card-desc">{item.description}</p>
                      <div className="attention-card-target">Appliance: {item.appliance}</div>
                    </div>

                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => onNavigate(item.targetTab, { issueId: item.issueId, applianceId: item.applianceId })}
                    >
                      {item.actionText}
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Two Column Layout: Recent Repairs & Quick Appliance Status */}
          <div className="overview-two-col">
            {/* Column 1: Recent Repairs */}
            <section className="content-panel">
              <div className="panel-header">
                <h2 className="panel-title">Recent Repairs & Maintenance</h2>
                <span
                  className="panel-action-link"
                  onClick={() => onNavigate('issues')}
                >
                  View all issues &rarr;
                </span>
              </div>

              {completedIssues.length > 0 ? (
                <table className="repairs-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Appliance & Service</th>
                      <th>Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedIssues.slice(0, 5).map((repair) => {
                      const app = appliances.find(a => a.id === repair.appliance_id);
                      return (
                        <tr key={repair.id}>
                          <td className="repair-date">{new Date(repair.resolved_at || repair.reported_at).toLocaleDateString()}</td>
                          <td>
                            <div className="repair-appliance-name">{app ? app.name : 'Unknown Appliance'}</div>
                            <div className="repair-type-text">{repair.title}</div>
                          </td>
                          <td>
                            <StatusBadge type="status" value={repair.repair_outcome || 'resolved'} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <p className="text-muted" style={{ padding: '16px' }}>No completed repairs found.</p>
              )}
            </section>

            {/* Column 2: Registered Appliances Quick Status */}
            <section className="content-panel">
              <div className="panel-header">
                <h2 className="panel-title">My Registered Appliances</h2>
                <span
                  className="panel-action-link"
                  onClick={() => onNavigate('appliances')}
                >
                  View all &rarr;
                </span>
              </div>

              {appliances.length > 0 ? (
                <div className="quick-appliance-list">
                  {appliances.map((appliance) => {
                    const hasActive = allIssues.some(
                      i => i.appliance_id === appliance.id && i.status !== 'resolved'
                    );
                    return (
                      <div 
                        key={appliance.id} 
                        className="quick-appliance-item"
                        style={{ cursor: 'pointer' }}
                        onClick={() => onNavigate('appliances', { applianceId: appliance.id })}
                      >
                        <div className="quick-appliance-main">
                          <span className={hasActive ? "status-dot-warning" : "status-dot-active"} title={hasActive ? "Active issue" : "Operational"} />
                          <div>
                            <div className="quick-appliance-name">{appliance.name}</div>
                            <div className="quick-appliance-model">{appliance.brand} &bull; {appliance.model_number}</div>
                          </div>
                        </div>

                        <div className="quick-appliance-meta">
                          {hasActive ? (
                            <StatusBadge type="severity" value="high" label="Need to Fix Issue" />
                          ) : (
                            <StatusBadge type="status" value="resolved" label="Nominal" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ padding: '24px', textAlign: 'center' }}>
                  <p className="text-muted" style={{ marginBottom: '16px' }}>No appliances registered yet.</p>
                  <button type="button" className="btn btn-primary" onClick={() => onNavigate('appliances')}>Add Appliance</button>
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}

export default OverviewPage;
