import React, { useState } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import { MOCK_APPLIANCES, MOCK_ISSUES } from '../utils/mockData';
import './AIInvestigationPage.css';

export function AIInvestigationPage({ initialApplianceId, initialIssueId }) {
  const [selectedApplianceId, setSelectedApplianceId] = useState(
    initialApplianceId ? Number(initialApplianceId) : MOCK_APPLIANCES[1].id // Default to Whirlpool Washer
  );

  const [selectedIssueId, setSelectedIssueId] = useState(
    initialIssueId ? Number(initialIssueId) : MOCK_ISSUES[0].id // Default to vibration issue
  );

  const activeAppliance =
    MOCK_APPLIANCES.find((a) => a.id === Number(selectedApplianceId)) ||
    MOCK_APPLIANCES[0];

  const activeIssue =
    MOCK_ISSUES.find((i) => i.id === Number(selectedIssueId)) ||
    MOCK_ISSUES[0];

  const applianceIssues = MOCK_ISSUES.filter(
    (i) => i.appliance_id === Number(selectedApplianceId)
  );

  return (
    <div className="ai-investigation-page">
      <PageHeader
        pretitle="Diagnostic System"
        title="AI Diagnostic Investigation"
        subtitle="Technical diagnostic investigation workbench, evidence correlation, manual lookup, and guided repair strategy."
      />

      <div className="investigation-workbench">
        {/* Phase notice clearly communicating architecture */}
        <div className="phase-notice-banner">
          <span className="phase-notice-badge">Architecture Stage</span>
          <span>
            Diagnostic workbench layout initialized. Autonomous LangGraph agent reasoning engine will be connected in future phase.
          </span>
        </div>

        {/* Appliance & Fault Context Selection */}
        <div className="investigation-selector-bar">
          <div className="selector-group">
            <label className="selector-label">Target Appliance:</label>
            <select
              className="selector-select"
              value={selectedApplianceId}
              onChange={(e) => {
                const nextApplianceId = Number(e.target.value);
                setSelectedApplianceId(nextApplianceId);
                const nextIssues = MOCK_ISSUES.filter(
                  (i) => i.appliance_id === nextApplianceId
                );
                if (nextIssues.length > 0) {
                  setSelectedIssueId(nextIssues[0].id);
                }
              }}
            >
              {MOCK_APPLIANCES.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.brand} {a.name} ({a.model_number})
                </option>
              ))}
            </select>
          </div>

          <div className="selector-group">
            <label className="selector-label">Active Issue:</label>
            <select
              className="selector-select"
              value={selectedIssueId}
              onChange={(e) => setSelectedIssueId(Number(e.target.value))}
            >
              {applianceIssues.length > 0 ? (
                applianceIssues.map((issue) => (
                  <option key={issue.id} value={issue.id}>
                    #{issue.id} - {issue.title}
                  </option>
                ))
              ) : (
                <option value="">No open issues for this appliance</option>
              )}
            </select>
          </div>
        </div>

        {/* Two-Column Workbench Layout */}
        <div className="workbench-layout">
          {/* Column 1: Appliance Specs & Evidence Collection */}
          <div className="workbench-column">
            {/* Appliance Profile Card */}
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">1</span>
                  <h2 className="card-title">Appliance Technical Profile</h2>
                </div>
                <StatusBadge type="status" value={activeAppliance.category} />
              </div>

              <div className="tech-spec-grid">
                <div className="tech-spec-item">
                  <span className="tech-spec-label">Brand</span>
                  <span className="tech-spec-val">{activeAppliance.brand}</span>
                </div>
                <div className="tech-spec-item">
                  <span className="tech-spec-label">Model Identifier</span>
                  <span className="tech-spec-val" style={{ fontFamily: 'var(--font-mono)' }}>
                    {activeAppliance.model_number}
                  </span>
                </div>
                <div className="tech-spec-item">
                  <span className="tech-spec-label">Location</span>
                  <span className="tech-spec-val">{activeAppliance.location}</span>
                </div>
                <div className="tech-spec-item">
                  <span className="tech-spec-label">Warranty Expiry</span>
                  <span className="tech-spec-val">{activeAppliance.warranty_expiry || 'None'}</span>
                </div>
              </div>

              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                {activeAppliance.notes}
              </p>
            </div>

            {/* Evidence & Symptoms Card */}
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">2</span>
                  <h2 className="card-title">Reported Symptom Evidence</h2>
                </div>
                {activeIssue && (
                  <StatusBadge type="severity" value={activeIssue.severity} />
                )}
              </div>

              {activeIssue ? (
                <>
                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                      {activeIssue.title}
                    </div>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.45 }}>
                      {activeIssue.description}
                    </p>
                  </div>

                  <div className="symptom-entry-list">
                    {activeIssue.symptoms && activeIssue.symptoms.map((s) => (
                      <div key={s.id} className="symptom-entry-row">
                        <span className="symptom-key">{s.name}</span>
                        <span className="symptom-reading">{s.value} {s.unit || ''}</span>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ width: '100%', fontSize: '0.75rem' }}
                    onClick={() => alert('Symptom entry modal will be activated in next phase.')}
                  >
                    + Record Additional Symptom Reading
                  </button>
                </>
              ) : (
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                  No active issue selected.
                </p>
              )}
            </div>
          </div>

          {/* Column 2: Diagnostic Reasoning Pipeline */}
          <div className="workbench-column">
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">3</span>
                  <h2 className="card-title">Diagnostic Reasoning Pipeline</h2>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  4 Stages Planned
                </span>
              </div>

              <div className="pipeline-steps">
                {/* Stage 1: OEM Manual Lookup */}
                <div className="pipeline-step">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-name">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                      </svg>
                      1. OEM Manual & Service Bulletin Lookup
                    </span>
                    <span className="pipeline-step-status">Schematic Indexed</span>
                  </div>
                  <div className="pipeline-step-body">
                    Matched Whirlpool Factory Service Manual W11184320. Fault isolation index verified for high-RPM vibration charts.
                  </div>
                </div>

                {/* Stage 2: Hypothesis Generation */}
                <div className="pipeline-step">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-name">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                      </svg>
                      2. Diagnostic Hypothesis Generation
                    </span>
                    <span className="pipeline-step-status">Confidence: 89%</span>
                  </div>
                  <div className="pipeline-step-body">
                    Correlation of 88 dB noise and tub slack points to:
                    <div className="hypothesis-item">
                      <strong>Primary:</strong> Failed rear drum suspension damper struts (Part #W10738125).
                    </div>
                    <div className="hypothesis-item" style={{ borderColor: 'var(--color-border-strong)' }}>
                      <strong>Secondary:</strong> Unbalanced counterweight or loose shipping bracket remnant.
                    </div>
                  </div>
                </div>

                {/* Stage 3: Warranty Checking */}
                <div className="pipeline-step">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-name">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      3. Warranty & Parts Assessment
                    </span>
                    <span className="pipeline-step-status">Coverage Expired</span>
                  </div>
                  <div className="pipeline-step-body">
                    Whirlpool 1-year limited warranty expired on June 20, 2022. Estimated DIY replacement parts cost: $42 - $65. Professional technician service: $180 - $240.
                  </div>
                </div>

                {/* Stage 4: Recommendation & Coordination */}
                <div className="pipeline-step">
                  <div className="pipeline-step-header">
                    <span className="pipeline-step-name">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9 11 12 14 22 4" />
                        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                      </svg>
                      4. Repair Recommendation & Service Coordination
                    </span>
                    <span className="pipeline-step-status">Action Ready</span>
                  </div>
                  <div className="pipeline-step-body">
                    Structured repair plan generated: Order OEM 4-pack damper kit, remove lower back panel with 1/4-inch nut driver, test damper friction pins.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AIInvestigationPage;
