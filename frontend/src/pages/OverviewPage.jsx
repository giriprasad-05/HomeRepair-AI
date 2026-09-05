import React from 'react';
import PageHeader from '../components/PageHeader';
import Metric from '../components/Metric';
import StatusBadge from '../components/StatusBadge';
import {
  MOCK_APPLIANCES,
  MOCK_REPAIRS,
  MOCK_METRICS,
  MOCK_ATTENTION_ITEMS,
} from '../utils/mockData';
import './OverviewPage.css';

export function OverviewPage({ onNavigate }) {
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
              className="btn btn-secondary"
              onClick={() => onNavigate('appliances')}
            >
              Manage Appliances
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onNavigate('investigation')}
            >
              Start Investigation
            </button>
          </>
        }
      />

      {/* Structured Metrics Grid */}
      <section className="overview-grid-metrics" aria-label="System Metrics">
        <Metric
          label="Active Appliances"
          value={MOCK_METRICS.active_appliances}
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
          value={MOCK_METRICS.open_issues}
          subtitle="Requires troubleshooting"
          trend="Action Needed"
          trendType="warning"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            </svg>
          }
        />
        <Metric
          label="Repairs in Progress"
          value={MOCK_METRICS.repairs_in_progress}
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
          value={MOCK_METRICS.upcoming_warranty_expiries}
          subtitle="Within 30 days"
          trend="Review Warranty"
          trendType="warning"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          }
        />
        <Metric
          label="Recent Repairs"
          value={MOCK_METRICS.completed_repairs}
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
      <section className="attention-section">
        <div className="attention-header">
          <svg className="attention-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h2 className="attention-title">Need Attention</h2>
          <span className="attention-badge-count">{MOCK_ATTENTION_ITEMS.length} items</span>
        </div>

        <div className="attention-list">
          {MOCK_ATTENTION_ITEMS.map((item) => (
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

          <table className="repairs-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Appliance & Service</th>
                <th>Outcome</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_REPAIRS.slice(0, 3).map((repair) => (
                <tr key={repair.id}>
                  <td className="repair-date">{repair.repair_date}</td>
                  <td>
                    <div className="repair-appliance-name">{repair.appliance_name}</div>
                    <div className="repair-type-text">{repair.repair_type}</div>
                  </td>
                  <td>
                    <StatusBadge type="status" value={repair.outcome} />
                  </td>
                  <td className="repair-cost">
                    {repair.service_cost === 0 ? 'Warranty / Free' : `$${repair.service_cost.toFixed(2)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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

          <div className="quick-appliance-list">
            {MOCK_APPLIANCES.map((appliance) => (
              <div key={appliance.id} className="quick-appliance-item">
                <div className="quick-appliance-main">
                  <span className="status-dot-active" title="Active in system" />
                  <div>
                    <div className="quick-appliance-name">{appliance.name}</div>
                    <div className="quick-appliance-model">{appliance.brand} &bull; {appliance.model_number}</div>
                  </div>
                </div>

                <div className="quick-appliance-meta">
                  {appliance.open_issue_count > 0 ? (
                    <StatusBadge type="severity" value="high" label={`${appliance.open_issue_count} issue`} />
                  ) : (
                    <StatusBadge type="status" value="resolved" label="Nominal" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default OverviewPage;
