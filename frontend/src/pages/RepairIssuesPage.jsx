import React, { useState } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import { MOCK_ISSUES } from '../utils/mockData';
import './RepairIssuesPage.css';

export function RepairIssuesPage({ onNavigate, filterApplianceId }) {
  const [activeFilter, setActiveFilter] = useState('all');

  const filteredIssues = MOCK_ISSUES.filter((issue) => {
    const matchesAppliance =
      !filterApplianceId || issue.appliance_id === Number(filterApplianceId);
    const matchesStatus =
      activeFilter === 'all' || issue.status === activeFilter;
    return matchesAppliance && matchesStatus;
  });

  return (
    <div className="repair-issues-page">
      <PageHeader
        pretitle="Troubleshooting"
        title="Appliance Repair Issues"
        subtitle="Reported malfunctions, recorded symptoms, diagnostic investigation progress, and corrective actions."
        actions={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate('investigation')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Report New Issue
          </button>
        }
      />

      {/* Filter Tabs */}
      <div className="issues-filter-tabs">
        <button
          type="button"
          className={`tab-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Issues ({MOCK_ISSUES.length})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeFilter === 'open' ? 'active' : ''}`}
          onClick={() => setActiveFilter('open')}
        >
          Open
        </button>
        <button
          type="button"
          className={`tab-btn ${activeFilter === 'investigating' ? 'active' : ''}`}
          onClick={() => setActiveFilter('investigating')}
        >
          Investigating
        </button>
        <button
          type="button"
          className={`tab-btn ${activeFilter === 'repair_recommended' ? 'active' : ''}`}
          onClick={() => setActiveFilter('repair_recommended')}
        >
          Repair Recommended
        </button>
        <button
          type="button"
          className={`tab-btn ${activeFilter === 'resolved' ? 'active' : ''}`}
          onClick={() => setActiveFilter('resolved')}
        >
          Resolved
        </button>
      </div>

      {/* Issues Listing */}
      {filteredIssues.length === 0 ? (
        <EmptyState
          title="No issues found for this view"
          description="There are currently no reported problems matching the selected status filter."
          action={
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setActiveFilter('all')}
            >
              Show All Issues
            </button>
          }
        />
      ) : (
        <div className="issues-list">
          {filteredIssues.map((issue) => (
            <article key={issue.id} className="issue-card">
              <div className="issue-card-header">
                <div>
                  <div className="issue-meta-appliance">
                    {issue.appliance_brand} {issue.appliance_name} &bull; Model {issue.appliance_model} &bull; {issue.appliance_location}
                  </div>
                  <h2 className="issue-title">{issue.title}</h2>
                </div>

                <div className="issue-badges">
                  <StatusBadge type="severity" value={issue.severity} />
                  <StatusBadge type="status" value={issue.status} />
                </div>
              </div>

              <p className="issue-description">{issue.description}</p>

              {/* Structured Symptoms Chips */}
              {issue.symptoms && issue.symptoms.length > 0 && (
                <div className="issue-symptoms-panel">
                  <div className="symptoms-title">Recorded Diagnostic Symptoms ({issue.symptoms.length})</div>
                  <div className="symptoms-chips">
                    {issue.symptoms.map((s) => (
                      <span key={s.id} className="symptom-chip">
                        <span className="symptom-chip-name">{s.name}:</span>
                        <span className="symptom-chip-value">
                          {s.value} {s.unit || ''}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="issue-card-footer">
                <span className="issue-reported-time">
                  Reported: {new Date(issue.reported_at).toLocaleDateString()} at {new Date(issue.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>

                <div className="issue-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() =>
                      onNavigate('investigation', {
                        issueId: issue.id,
                        applianceId: issue.appliance_id,
                      })
                    }
                  >
                    Open Diagnostic Session &rarr;
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default RepairIssuesPage;
