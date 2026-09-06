import React, { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import { ApplianceService, IssueService, AgentService } from '../services/api';
import './AIInvestigationPage.css';

// Simulated timeline steps for the UX
const AGENT_STEPS = [
  "Loaded appliance history",
  "Retrieved previous repair memory",
  "Analyzed reported symptoms",
  "Checked warranty",
  "Reviewed historical repair outcomes",
  "Evaluated diagnostic evidence",
  "Preparing recommendation..."
];

export function AIInvestigationPage({ initialApplianceId, initialIssueId } = {}) {
  const [appliances, setAppliances] = useState([]);
  const [issues, setIssues] = useState([]);
  const [selectedApplianceId, setSelectedApplianceId] = useState(
    initialApplianceId ? initialApplianceId.toString() : ''
  );
  const [selectedIssueId, setSelectedIssueId] = useState(
    initialIssueId ? initialIssueId.toString() : ''
  );

  const [applianceLoading, setApplianceLoading] = useState(true);
  const [issuesLoading, setIssuesLoading] = useState(false);
  const [error, setError] = useState('');

  // Investigation state
  // 'idle' | 'investigating' | 'success' | 'insufficient_data' | 'error'
  const [investigationState, setInvestigationState] = useState('idle');
  const [timelineStepIndex, setTimelineStepIndex] = useState(0);
  const [report, setReport] = useState(null);
  const [investigationError, setInvestigationError] = useState('');

  useEffect(() => {
    fetchAppliances();
  }, []);

  useEffect(() => {
    if (selectedApplianceId) {
      fetchIssues(selectedApplianceId);
    } else {
      setIssues([]);
      setSelectedIssueId('');
    }
  }, [selectedApplianceId]);

  const fetchAppliances = async () => {
    try {
      setApplianceLoading(true);
      const data = await ApplianceService.getAppliances();
      setAppliances(data);
      if (data.length > 0) {
        if (initialApplianceId && data.some(a => a.id.toString() === initialApplianceId.toString())) {
          setSelectedApplianceId(initialApplianceId.toString());
        } else if (!selectedApplianceId) {
          setSelectedApplianceId(data[0].id.toString());
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load appliances');
    } finally {
      setApplianceLoading(false);
    }
  };

  const fetchIssues = async (appId) => {
    try {
      setIssuesLoading(true);
      const data = await IssueService.getApplianceIssues(appId);
      setIssues(data);
      if (data.length > 0) {
        if (initialIssueId && data.some(i => i.id.toString() === initialIssueId.toString())) {
          setSelectedIssueId(initialIssueId.toString());
        } else {
          setSelectedIssueId(data[0].id.toString());
        }
      } else {
        setSelectedIssueId('');
      }
    } catch (err) {
      setError(err.message || 'Failed to load issues');
    } finally {
      setIssuesLoading(false);
    }
  };

  const handleInvestigate = async () => {
    if (!selectedIssueId) return;

    setInvestigationState('investigating');
    setTimelineStepIndex(0);
    setReport(null);
    setInvestigationError('');

    // Start a simulated progress timeline
    const timelineInterval = setInterval(() => {
      setTimelineStepIndex((prev) => {
        if (prev < AGENT_STEPS.length - 1) return prev + 1;
        return prev; // Stop at the last step ("Preparing recommendation...")
      });
    }, 1200);

    try {
      const data = await AgentService.investigate(selectedIssueId);
      clearInterval(timelineInterval);
      setTimelineStepIndex(AGENT_STEPS.length); // complete
      
      if (data.analysis_status === 'insufficient_data') {
        setInvestigationState('insufficient_data');
      } else {
        setInvestigationState('success');
      }
      setReport(data);
    } catch (err) {
      clearInterval(timelineInterval);
      setInvestigationState('error');
      setInvestigationError(err.message || 'Diagnostic agent failed to complete investigation.');
    }
  };

  const activeAppliance = appliances.find((a) => a.id.toString() === selectedApplianceId);
  const activeIssue = issues.find((i) => i.id.toString() === selectedIssueId);

  return (
    <div className="ai-investigation-page">
      <PageHeader
        pretitle="Diagnostic System"
        title="AI Diagnostic Investigation"
        subtitle="Technical diagnostic investigation workbench, evidence correlation, manual lookup, and guided repair strategy."
      />

      <div className="investigation-workbench">
        {/* Selectors */}
        <div className="investigation-selector-bar">
          <div className="selector-group">
            <label className="selector-label">Target Appliance:</label>
            <select
              className="selector-select"
              value={selectedApplianceId}
              onChange={(e) => setSelectedApplianceId(e.target.value)}
              disabled={applianceLoading || investigationState === 'investigating'}
            >
              {appliances.map((a) => (
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
              onChange={(e) => setSelectedIssueId(e.target.value)}
              disabled={issuesLoading || investigationState === 'investigating'}
            >
              {issues.length > 0 ? (
                issues.map((issue) => (
                  <option key={issue.id} value={issue.id}>
                    #{issue.id} - {issue.title}
                  </option>
                ))
              ) : (
                <option value="">No open issues</option>
              )}
            </select>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="workbench-layout">
          {/* Column 1: Context */}
          <div className="workbench-column">
            {/* Appliance Profile Card */}
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">1</span>
                  <h2 className="card-title">Appliance Context</h2>
                </div>
                {activeAppliance && <StatusBadge type="status" value={activeAppliance.category} />}
              </div>

              {activeAppliance ? (
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
                </div>
              ) : (
                <p className="text-muted">No appliance selected.</p>
              )}
            </div>

            {/* Issue Card */}
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">2</span>
                  <h2 className="card-title">Problem & Symptoms</h2>
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
                      {activeIssue.description || 'No detailed description provided.'}
                    </p>
                  </div>

                  <div className="symptom-entry-list">
                    {activeIssue.symptoms && activeIssue.symptoms.length > 0 ? (
                      activeIssue.symptoms.map((s) => (
                        <div key={s.id} className="symptom-entry-row">
                          <span className="symptom-key">{s.name}</span>
                          <span className="symptom-reading">{s.value} {s.unit || ''}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-muted">No recorded symptoms.</p>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-muted">No active issue selected.</p>
              )}
            </div>
            
            <button
              type="button"
              className="btn btn-primary investigate-btn"
              disabled={!activeIssue || investigationState === 'investigating'}
              onClick={handleInvestigate}
            >
              {investigationState === 'investigating' ? 'Investigating...' : 'Investigate Problem'}
            </button>
          </div>

          {/* Column 2: Agent Activity & Report */}
          <div className="workbench-column">
            <div className="workbench-card">
              <div className="workbench-card-header">
                <div className="card-title-group">
                  <span className="card-step-badge">3</span>
                  <h2 className="card-title">Investigation Report</h2>
                </div>
              </div>

              <div className="report-container">
                {investigationState === 'idle' && (
                  <div className="idle-state">
                    <p className="text-muted">Select an issue and click "Investigate Problem" to begin.</p>
                  </div>
                )}

                {investigationState === 'investigating' && (
                  <div className="investigating-state">
                    <h3>Investigating Problem</h3>
                    <div className="timeline-container">
                      {AGENT_STEPS.map((step, idx) => (
                        <div 
                          key={idx} 
                          className={`timeline-step ${idx < timelineStepIndex ? 'completed' : idx === timelineStepIndex ? 'active' : 'pending'}`}
                        >
                          <span className="timeline-icon">
                            {idx < timelineStepIndex ? '✓' : idx === timelineStepIndex ? '●' : '○'}
                          </span>
                          <span className="timeline-text">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {investigationState === 'error' && (
                  <div className="error-state">
                    <h3>Investigation Failed</h3>
                    <p>{investigationError}</p>
                    <button className="btn btn-secondary" onClick={handleInvestigate}>Retry</button>
                  </div>
                )}

                {(investigationState === 'success' || investigationState === 'insufficient_data') && report && (
                  <div className="report-content">
                    
                    {investigationState === 'insufficient_data' && (
                      <div className="warning-banner">
                        <strong>Insufficient Data:</strong> {report.summary}
                      </div>
                    )}
                    
                    {investigationState === 'success' && (
                      <div className="report-section">
                        <h3>Problem Summary</h3>
                        <p>{report.summary}</p>
                      </div>
                    )}

                    {report.likely_causes && report.likely_causes.length > 0 && (
                      <div className="report-section">
                        <h3>Possible Causes</h3>
                        <ul className="causes-list">
                          {report.likely_causes.map((cause, idx) => (
                            <li key={idx} className={`cause-item ${cause.confidence.toLowerCase()}`}>
                              <div className="cause-header">
                                <strong>{cause.cause}</strong>
                                <span className={`confidence-badge ${cause.confidence.toLowerCase()}`}>
                                  {cause.confidence}
                                </span>
                              </div>
                              <p className="cause-reason">{cause.reason}</p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {report.evidence && report.evidence.length > 0 && (
                      <div className="report-section">
                        <h3>Evidence</h3>
                        <ul className="evidence-list">
                          {report.evidence.map((ev, idx) => (
                            <li key={idx}>
                              <strong>{ev.observation}</strong>: {ev.supports}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {report.uncertainty && report.uncertainty !== "No critical uncertainties identified." && (
                      <div className="report-section">
                        <h3>What Is Still Uncertain</h3>
                        <p className="uncertainty-text">{report.uncertainty}</p>
                      </div>
                    )}

                    <div className="report-section">
                      <h3>Recommended Next Step</h3>
                      <p className="next-step-box">{report.recommended_next_step}</p>
                    </div>

                    <div className="report-section row-split">
                      <div className="split-item">
                        <h3>Service Recommendation</h3>
                        <p>{report.service_recommendation}</p>
                      </div>
                      <div className="split-item">
                        <h3>Warranty Status</h3>
                        <p>{report.warranty_recommendation || report.warranty_status}</p>
                      </div>
                    </div>

                    {report.repair_history && report.repair_history.length > 0 && (
                      <div className="report-section">
                        <h3>Repair History Context</h3>
                        <ul className="repair-history-list">
                          {report.repair_history.map((rh, idx) => (
                            <li key={idx}>{rh}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AIInvestigationPage;
